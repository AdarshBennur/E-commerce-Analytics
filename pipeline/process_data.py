#!/usr/bin/env python3
"""
Product Analytics Dashboard — Data Processing Pipeline (simplified variant)
============================================================================
ONE-TIME OFFLINE STEP — Do NOT import or run this from the application server.

Run manually once after creating the sample dataset:
    python3 pipeline/create_sample_dataset.py   # creates data_sample/2019-Nov-sample.csv
    python3 pipeline/process_data.py             # generates analytics/*.parquet

Input  : data_sample/2019-Nov-sample.csv  (~1 M rows, created by create_sample_dataset.py)
         NEVER reads from /data — raw CSV files must never be loaded at runtime.
Output : analytics/funnel_metrics.parquet
         analytics/daily_active_users.parquet
         analytics/revenue_metrics.parquet
         analytics/category_performance.parquet
         analytics/conversion_metrics.parquet

After this script finishes, the /data_sample directory is NEVER accessed again
at runtime. The dashboard reads ONLY from /analytics.
"""

import os
import sys
import time
import duckdb

# Hard block: this module must never be imported by the FastAPI backend.
if __name__ != "__main__":
    raise ImportError(
        "pipeline/process_data.py is a standalone preprocessing script. "
        "It must not be imported by the application. "
        "Run it once with: python3 pipeline/process_data.py"
    )

# ─── PATHS ────────────────────────────────────────────────────────────────────
ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Use the sample dataset — NOT the raw 8.4 GB /data directory.
DATA_FILE   = os.path.join(ROOT, "data_sample", "2019-Nov-sample.csv")
OUT_DIR     = os.path.join(ROOT, "analytics")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}]  {msg}", flush=True)

def save(con: duckdb.DuckDBPyConnection, sql: str, filename: str):
    path = os.path.join(OUT_DIR, filename)
    log(f"  Saving {filename} ...")
    t0 = time.time()
    con.execute(f"COPY ({sql}) TO '{path}' (FORMAT PARQUET, COMPRESSION SNAPPY);")
    rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{path}')").fetchone()[0]
    log(f"  ✓  {filename} — {rows:,} rows  ({time.time()-t0:.1f}s)")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    t_total = time.time()

    log("=" * 58)
    log("Product Analytics Dashboard — Preprocessing Pipeline")
    log(f"Source : {DATA_FILE}")
    log(f"Output : {OUT_DIR}")
    log("=" * 58)

    # Guard: refuse to run if the sample file hasn't been created yet.
    if not os.path.isfile(DATA_FILE):
        print(
            f"\nERROR: Sample file not found:\n  {DATA_FILE}\n\n"
            "Generate it first:\n"
            "  python3 pipeline/create_sample_dataset.py\n",
            file=sys.stderr,
        )
        sys.exit(1)

    sample_mb = os.path.getsize(DATA_FILE) / 1e6
    log(f"Sample file size: {sample_mb:.1f} MB")

    # ── Connect — memory-safe settings for a 100 K-row dataset ───────────────
    con = duckdb.connect()
    con.execute("SET threads TO 2;")
    con.execute("SET memory_limit = '512MB';")
    con.execute("SET temp_directory = '/tmp/duckdb_tmp';")
    os.makedirs("/tmp/duckdb_tmp", exist_ok=True)

    # ── Base view — reads ONLY from data_sample/, never from /data ────────────
    # Includes all derived columns (event_date, category_main) required by the
    # backend routers so the generated Parquet schemas exactly match.
    log("Loading sample event data ...")
    con.execute(f"""
        CREATE OR REPLACE VIEW events AS
        SELECT
            CAST(event_time AS TIMESTAMP)                              AS event_time,
            DATE_TRUNC('day', CAST(event_time AS TIMESTAMP))::DATE     AS event_date,
            event_type,
            CAST(product_id AS BIGINT)                                 AS product_id,
            COALESCE(NULLIF(TRIM(category_code), ''), 'unknown')       AS category_code,
            SPLIT_PART(
                COALESCE(NULLIF(TRIM(category_code), ''), 'unknown'),
                '.', 1
            )                                                          AS category_main,
            COALESCE(NULLIF(TRIM(brand), ''), 'unknown')               AS brand,
            CASE WHEN TRY_CAST(price AS DOUBLE) >= 0
                 THEN CAST(price AS DOUBLE) ELSE 0 END                 AS price,
            CAST(user_id AS BIGINT)                                    AS user_id,
            user_session
        FROM read_csv_auto(
            '{DATA_FILE}',
            header        = true,
            ignore_errors = true,
            parallel      = false
        )
        WHERE event_type IN ('view', 'cart', 'purchase')
          AND user_id  IS NOT NULL
          AND product_id IS NOT NULL
    """)
    log("  ✓  Events view ready\n")

    # ── 1. Daily Active Users ─────────────────────────────────────────────────
    # Schema: event_date, dau, sessions, views, carts, purchases, revenue
    log("Generating daily_active_users ...")
    save(con, """
        SELECT
            event_date,
            COUNT(DISTINCT user_id)                                         AS dau,
            COUNT(DISTINCT user_session)                                    AS sessions,
            COUNT(*) FILTER (WHERE event_type = 'view')                     AS views,
            COUNT(*) FILTER (WHERE event_type = 'cart')                     AS carts,
            COUNT(*) FILTER (WHERE event_type = 'purchase')                 AS purchases,
            COALESCE(SUM(price) FILTER (WHERE event_type = 'purchase'), 0)  AS revenue
        FROM events
        GROUP BY event_date
        ORDER BY event_date
    """, "daily_active_users.parquet")

    # ── 2. Funnel Metrics ─────────────────────────────────────────────────────
    # Schema: event_date, category_main, brand, viewers, carted, purchasers,
    #         view_events, cart_events, purchase_events,
    #         view_to_cart_pct, cart_to_purchase_pct, overall_conversion_pct
    log("\nGenerating funnel_metrics ...")
    save(con, """
        WITH stage_counts AS (
            SELECT
                event_date,
                category_main,
                brand,
                COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'view')     AS viewers,
                COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'cart')     AS carted,
                COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'purchase') AS purchasers,
                COUNT(*) FILTER (WHERE event_type = 'view')                    AS view_events,
                COUNT(*) FILTER (WHERE event_type = 'cart')                    AS cart_events,
                COUNT(*) FILTER (WHERE event_type = 'purchase')                AS purchase_events
            FROM events
            GROUP BY event_date, category_main, brand
        )
        SELECT
            *,
            CASE WHEN viewers > 0
                 THEN ROUND(100.0 * carted / viewers, 2) ELSE 0 END     AS view_to_cart_pct,
            CASE WHEN carted > 0
                 THEN ROUND(100.0 * purchasers / carted, 2) ELSE 0 END  AS cart_to_purchase_pct,
            CASE WHEN viewers > 0
                 THEN ROUND(100.0 * purchasers / viewers, 2) ELSE 0 END AS overall_conversion_pct
        FROM stage_counts
    """, "funnel_metrics.parquet")

    # ── 3. Revenue Metrics ────────────────────────────────────────────────────
    # Schema: event_date, category_main, brand, orders, revenue,
    #         avg_order_value, unique_buyers
    log("\nGenerating revenue_metrics ...")
    save(con, """
        SELECT
            event_date,
            category_main,
            brand,
            COUNT(*) FILTER (WHERE event_type = 'purchase')                    AS orders,
            COALESCE(SUM(price) FILTER (WHERE event_type = 'purchase'), 0)     AS revenue,
            COALESCE(AVG(price) FILTER (WHERE event_type = 'purchase'), 0)     AS avg_order_value,
            COUNT(DISTINCT user_id) FILTER (WHERE event_type = 'purchase')     AS unique_buyers
        FROM events
        GROUP BY event_date, category_main, brand
        ORDER BY event_date
    """, "revenue_metrics.parquet")

    # ── 4. Category Performance ───────────────────────────────────────────────
    # Schema: category_main, category_code, total_users, views, carts,
    #         purchases, revenue, avg_price, conversion_rate
    log("\nGenerating category_performance ...")
    save(con, """
        WITH cat_agg AS (
            SELECT
                category_main,
                category_code,
                COUNT(DISTINCT user_id)                                             AS total_users,
                COUNT(*) FILTER (WHERE event_type = 'view')                         AS views,
                COUNT(*) FILTER (WHERE event_type = 'cart')                         AS carts,
                COUNT(*) FILTER (WHERE event_type = 'purchase')                     AS purchases,
                COALESCE(SUM(price)  FILTER (WHERE event_type = 'purchase'), 0)     AS revenue,
                COALESCE(AVG(price)  FILTER (WHERE event_type = 'purchase'), 0)     AS avg_price
            FROM events
            WHERE category_main != 'unknown'
            GROUP BY category_main, category_code
        )
        SELECT
            *,
            CASE WHEN views > 0
                 THEN ROUND(100.0 * purchases / views, 3) ELSE 0 END AS conversion_rate
        FROM cat_agg
        ORDER BY revenue DESC
    """, "category_performance.parquet")

    # ── 5. Brand Performance ──────────────────────────────────────────────────
    # Schema: brand, total_users, views, carts, purchases, revenue,
    #         avg_price, conversion_rate
    log("\nGenerating brand_performance ...")
    save(con, """
        WITH brand_agg AS (
            SELECT
                brand,
                COUNT(DISTINCT user_id)                                             AS total_users,
                COUNT(*) FILTER (WHERE event_type = 'view')                         AS views,
                COUNT(*) FILTER (WHERE event_type = 'cart')                         AS carts,
                COUNT(*) FILTER (WHERE event_type = 'purchase')                     AS purchases,
                COALESCE(SUM(price)  FILTER (WHERE event_type = 'purchase'), 0)     AS revenue,
                COALESCE(AVG(price)  FILTER (WHERE event_type = 'purchase'), 0)     AS avg_price
            FROM events
            WHERE brand != 'unknown'
            GROUP BY brand
        )
        SELECT
            *,
            CASE WHEN views > 0
                 THEN ROUND(100.0 * purchases / views, 3) ELSE 0 END AS conversion_rate
        FROM brand_agg
        ORDER BY revenue DESC
    """, "brand_performance.parquet")

    # ── 6. Filter Catalogs ────────────────────────────────────────────────────
    # Schema: value, event_count
    log("\nGenerating filter_categories ...")
    save(con, """
        SELECT category_main AS value, COUNT(*) AS event_count
        FROM events
        WHERE category_main != 'unknown' AND category_main != ''
        GROUP BY category_main
        ORDER BY event_count DESC
        LIMIT 100
    """, "filter_categories.parquet")

    log("\nGenerating filter_brands ...")
    save(con, """
        SELECT brand AS value, COUNT(*) AS event_count
        FROM events
        WHERE brand != 'unknown' AND brand != ''
        GROUP BY brand
        ORDER BY event_count DESC
        LIMIT 200
    """, "filter_brands.parquet")

    # ── 7. Conversion Metrics ─────────────────────────────────────────────────
    log("\nGenerating conversion_metrics ...")
    save(con, """
        WITH counts AS (
            SELECT
                COUNT(*) FILTER (WHERE event_type = 'view')     AS views,
                COUNT(*) FILTER (WHERE event_type = 'cart')     AS carts,
                COUNT(*) FILTER (WHERE event_type = 'purchase') AS purchases
            FROM events
        )
        SELECT
            views, carts, purchases,
            ROUND(100.0 * carts     / NULLIF(views, 0), 4) AS view_to_cart_conversion,
            ROUND(100.0 * purchases / NULLIF(carts, 0), 4) AS cart_to_purchase_conversion
        FROM counts
    """, "conversion_metrics.parquet")

    # ── Done ───────────────────────────────────────────────────────────────────
    log("\n" + "=" * 58)
    log(f"Pipeline complete in {time.time()-t_total:.1f}s")
    log("Output tables:")
    total_bytes = 0
    for f in sorted(os.listdir(OUT_DIR)):
        if f.endswith(".parquet"):
            sz = os.path.getsize(os.path.join(OUT_DIR, f))
            total_bytes += sz
            if sz >= 1_048_576:
                label = f"{sz / 1_048_576:.1f} MB"
            else:
                label = f"{sz // 1024} KB"
            log(f"  analytics/{f}  ({label})")
    log(f"  ── Total: {total_bytes / 1_048_576:.2f} MB")
    log("")
    log("Runtime data source: analytics/*.parquet  (raw CSV is NEVER read by the app)")
    log("=" * 58)

    con.close()

if __name__ == "__main__":
    main()
