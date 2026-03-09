#!/usr/bin/env python3
"""
Product Analytics Dashboard — Data Preprocessing Pipeline
==========================================================
ONE-TIME OFFLINE STEP — Do NOT import or run this from the application server.

Run manually once to generate the analytics Parquet tables:
    npm run pipeline          # from the repo root
    python3 pipeline/preprocess.py   # directly

Input  : data/2019-Oct.csv, data/2019-Nov.csv  (~285M rows, streamed via DuckDB)
Output : analytics/*.parquet  (14 small aggregated tables)

After this script finishes, the /data directory is NEVER accessed again at runtime.
"""

import os
import sys
import time
import duckdb

# Hard block: this module must never be imported by the FastAPI backend.
if __name__ != "__main__":
    raise ImportError(
        "pipeline/preprocess.py is a standalone preprocessing script. "
        "It must not be imported by the application. "
        "Run it once with: python3 pipeline/preprocess.py"
    )

# ───────────────────────────────────────────────────────────────────────────────
# PATHS
# ───────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
ANALYTICS_DIR = os.path.join(ROOT_DIR, "analytics")

os.makedirs(ANALYTICS_DIR, exist_ok=True)

CSV_GLOB = os.path.join(DATA_DIR, "*.csv")

def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ───────────────────────────────────────────────────────────────────────────────
# INITIALIZE DUCKDB
# ───────────────────────────────────────────────────────────────────────────────
def get_connection() -> duckdb.DuckDBPyConnection:
    """Create an in-process DuckDB connection with threading and memory settings."""
    con = duckdb.connect()
    con.execute("SET threads TO 8;")
    con.execute("SET memory_limit = '8GB';")
    con.execute("SET temp_directory = '/tmp/duckdb_tmp';")
    os.makedirs("/tmp/duckdb_tmp", exist_ok=True)
    return con


# ───────────────────────────────────────────────────────────────────────────────
# STEP 1: CREATE BASE EVENTS VIEW
# ───────────────────────────────────────────────────────────────────────────────
def create_events_view(con: duckdb.DuckDBPyConnection):
    log("Creating base events view over CSV files...")
    con.execute(f"""
        CREATE OR REPLACE VIEW raw_events AS
        SELECT
            CAST(event_time AS TIMESTAMP) AS event_time,
            event_type,
            CAST(product_id AS BIGINT) AS product_id,
            CAST(category_id AS BIGINT) AS category_id,
            COALESCE(NULLIF(TRIM(category_code), ''), 'unknown') AS category_code,
            COALESCE(NULLIF(TRIM(brand), ''), 'unknown') AS brand,
            CAST(price AS DOUBLE) AS price,
            CAST(user_id AS BIGINT) AS user_id,
            user_session
        FROM read_csv_auto(
            '{CSV_GLOB}',
            header=true,
            ignore_errors=true,
            parallel=true
        )
        WHERE event_type IN ('view', 'cart', 'purchase')
          AND price >= 0
          AND user_id IS NOT NULL
          AND product_id IS NOT NULL
    """)

    # Create enriched view with derived columns
    con.execute("""
        CREATE OR REPLACE VIEW events AS
        SELECT
            *,
            DATE_TRUNC('day', event_time) AS event_date,
            DATE_TRUNC('week', event_time) AS event_week,
            DATE_TRUNC('month', event_time) AS event_month,
            SPLIT_PART(category_code, '.', 1) AS category_main,
            SPLIT_PART(category_code, '.', 2) AS category_sub
        FROM raw_events
    """)
    log("Events view created OK.")


# ───────────────────────────────────────────────────────────────────────────────
# TABLE GENERATORS
# ───────────────────────────────────────────────────────────────────────────────
def save_table(con: duckdb.DuckDBPyConnection, query: str, name: str):
    out_path = os.path.join(ANALYTICS_DIR, f"{name}.parquet")
    log(f"Generating {name}...")
    t0 = time.time()
    con.execute(f"COPY ({query}) TO '{out_path}' (FORMAT PARQUET, COMPRESSION SNAPPY);")
    rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out_path}')").fetchone()[0]
    log(f"  ✓ {name}: {rows:,} rows [{time.time()-t0:.1f}s]")


def generate_daily_active_users(con):
    save_table(con, """
        SELECT
            event_date,
            COUNT(DISTINCT user_id) AS dau,
            COUNT(DISTINCT user_session) AS sessions,
            COUNT(*) FILTER (WHERE event_type='view') AS views,
            COUNT(*) FILTER (WHERE event_type='cart') AS carts,
            COUNT(*) FILTER (WHERE event_type='purchase') AS purchases,
            COALESCE(SUM(price) FILTER (WHERE event_type='purchase'), 0) AS revenue
        FROM events
        GROUP BY event_date
        ORDER BY event_date
    """, "daily_active_users")


def generate_weekly_active_users(con):
    save_table(con, """
        SELECT
            event_week,
            COUNT(DISTINCT user_id) AS wau,
            COUNT(DISTINCT user_session) AS sessions,
            COALESCE(SUM(price) FILTER (WHERE event_type='purchase'), 0) AS revenue
        FROM events
        GROUP BY event_week
        ORDER BY event_week
    """, "weekly_active_users")


def generate_session_summary(con):
    """
    Single-row aggregate of session statistics.
    The backend /api/behavior endpoint reads THIS table for KPI cards instead
    of scanning the 1.3 GB session_metrics.parquet file.
    """
    save_table(con, """
        WITH session_events AS (
            SELECT
                user_session,
                user_id,
                event_date,
                MIN(event_time) AS session_start,
                MAX(event_time) AS session_end,
                COUNT(*) AS total_events,
                COUNT(*) FILTER (WHERE event_type='view') AS view_count,
                COUNT(*) FILTER (WHERE event_type='purchase') AS purchase_count,
                COUNT(DISTINCT product_id) AS unique_products
            FROM events
            GROUP BY user_session, user_id, event_date
        )
        SELECT
            COUNT(*)                                                        AS total_sessions,
            ROUND(AVG(view_count), 2)                                      AS avg_views_per_session,
            ROUND(AVG(unique_products), 2)                                 AS avg_products_per_session,
            ROUND(AVG(DATEDIFF('minute', session_start, session_end)), 2)  AS avg_session_duration_min,
            ROUND(AVG(total_events), 2)                                    AS avg_events_per_session,
            ROUND(100.0 * SUM(CASE WHEN purchase_count > 0 THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0), 3)                                AS session_conversion_rate
        FROM session_events
    """, "session_summary")


def generate_session_metrics(con):
    save_table(con, """
        WITH session_events AS (
            SELECT
                user_session,
                user_id,
                event_date,
                MIN(event_time) AS session_start,
                MAX(event_time) AS session_end,
                COUNT(*) AS total_events,
                COUNT(*) FILTER (WHERE event_type='view') AS view_count,
                COUNT(*) FILTER (WHERE event_type='cart') AS cart_count,
                COUNT(*) FILTER (WHERE event_type='purchase') AS purchase_count,
                COALESCE(SUM(price) FILTER (WHERE event_type='purchase'), 0) AS session_revenue,
                COUNT(DISTINCT product_id) AS unique_products
            FROM events
            GROUP BY user_session, user_id, event_date
        )
        SELECT
            *,
            DATEDIFF('minute', session_start, session_end) AS session_duration_minutes,
            purchase_count > 0 AS converted
        FROM session_events
    """, "session_metrics")


def generate_funnel_metrics(con):
    save_table(con, """
        WITH stage_counts AS (
            SELECT
                event_date,
                category_main,
                brand,
                COUNT(DISTINCT user_id) FILTER (WHERE event_type='view') AS viewers,
                COUNT(DISTINCT user_id) FILTER (WHERE event_type='cart') AS carted,
                COUNT(DISTINCT user_id) FILTER (WHERE event_type='purchase') AS purchasers,
                COUNT(*) FILTER (WHERE event_type='view') AS view_events,
                COUNT(*) FILTER (WHERE event_type='cart') AS cart_events,
                COUNT(*) FILTER (WHERE event_type='purchase') AS purchase_events
            FROM events
            GROUP BY event_date, category_main, brand
        )
        SELECT
            *,
            CASE WHEN viewers > 0 THEN ROUND(100.0 * carted / viewers, 2) ELSE 0 END AS view_to_cart_pct,
            CASE WHEN carted > 0 THEN ROUND(100.0 * purchasers / carted, 2) ELSE 0 END AS cart_to_purchase_pct,
            CASE WHEN viewers > 0 THEN ROUND(100.0 * purchasers / viewers, 2) ELSE 0 END AS overall_conversion_pct
        FROM stage_counts
    """, "funnel_metrics")


def generate_revenue_metrics(con):
    save_table(con, """
        SELECT
            event_date,
            category_main,
            brand,
            COUNT(*) FILTER (WHERE event_type='purchase') AS orders,
            COALESCE(SUM(price) FILTER (WHERE event_type='purchase'), 0) AS revenue,
            COALESCE(AVG(price) FILTER (WHERE event_type='purchase'), 0) AS avg_order_value,
            COUNT(DISTINCT user_id) FILTER (WHERE event_type='purchase') AS unique_buyers
        FROM events
        GROUP BY event_date, category_main, brand
        ORDER BY event_date
    """, "revenue_metrics")


def generate_category_performance(con):
    save_table(con, """
        WITH cat_agg AS (
            SELECT
                category_main,
                category_code,
                COUNT(DISTINCT user_id) AS total_users,
                COUNT(*) FILTER (WHERE event_type='view') AS views,
                COUNT(*) FILTER (WHERE event_type='cart') AS carts,
                COUNT(*) FILTER (WHERE event_type='purchase') AS purchases,
                COALESCE(SUM(price) FILTER (WHERE event_type='purchase'), 0) AS revenue,
                COALESCE(AVG(price) FILTER (WHERE event_type='purchase'), 0) AS avg_price
            FROM events
            WHERE category_main != 'unknown'
            GROUP BY category_main, category_code
        )
        SELECT
            *,
            CASE WHEN views > 0 THEN ROUND(100.0 * purchases / views, 3) ELSE 0 END AS conversion_rate
        FROM cat_agg
        ORDER BY revenue DESC
    """, "category_performance")


def generate_brand_performance(con):
    save_table(con, """
        WITH brand_agg AS (
            SELECT
                brand,
                COUNT(DISTINCT user_id) AS total_users,
                COUNT(*) FILTER (WHERE event_type='view') AS views,
                COUNT(*) FILTER (WHERE event_type='cart') AS carts,
                COUNT(*) FILTER (WHERE event_type='purchase') AS purchases,
                COALESCE(SUM(price) FILTER (WHERE event_type='purchase'), 0) AS revenue,
                COALESCE(AVG(price) FILTER (WHERE event_type='purchase'), 0) AS avg_price
            FROM events
            WHERE brand != 'unknown'
            GROUP BY brand
        )
        SELECT
            *,
            CASE WHEN views > 0 THEN ROUND(100.0 * purchases / views, 3) ELSE 0 END AS conversion_rate
        FROM brand_agg
        ORDER BY revenue DESC
    """, "brand_performance")


def generate_retention_cohorts(con):
    """
    Week-over-week cohort retention.
    cohort_week = the week of the user's FIRST event.
    activity_week = subsequent weeks where user returns.
    """
    save_table(con, """
        WITH first_seen AS (
            SELECT user_id, MIN(event_week) AS cohort_week
            FROM events
            GROUP BY user_id
        ),
        weekly_activity AS (
            SELECT DISTINCT e.user_id, e.event_week AS activity_week, f.cohort_week
            FROM events e
            JOIN first_seen f ON e.user_id = f.user_id
        ),
        cohort_sizes AS (
            SELECT cohort_week, COUNT(DISTINCT user_id) AS cohort_size
            FROM first_seen
            GROUP BY cohort_week
        )
        SELECT
            wa.cohort_week,
            wa.activity_week,
            cs.cohort_size,
            COUNT(DISTINCT wa.user_id) AS retained_users,
            ROUND(100.0 * COUNT(DISTINCT wa.user_id) / cs.cohort_size, 2) AS retention_pct,
            CAST(DATEDIFF('week', wa.cohort_week, wa.activity_week) AS INTEGER) AS week_number
        FROM weekly_activity wa
        JOIN cohort_sizes cs ON wa.cohort_week = cs.cohort_week
        WHERE wa.cohort_week >= '2019-10-01'
        GROUP BY wa.cohort_week, wa.activity_week, cs.cohort_size
        ORDER BY wa.cohort_week, wa.activity_week
    """, "retention_cohorts")


def generate_user_segments(con):
    """Classify users into behavioral segments."""
    save_table(con, """
        WITH user_stats AS (
            SELECT
                user_id,
                COUNT(DISTINCT user_session) AS total_sessions,
                COUNT(*) FILTER (WHERE event_type='view') AS total_views,
                COUNT(*) FILTER (WHERE event_type='purchase') AS total_purchases,
                COALESCE(SUM(price) FILTER (WHERE event_type='purchase'), 0) AS total_spend,
                COUNT(DISTINCT event_date) AS active_days,
                MIN(event_date) AS first_seen,
                MAX(event_date) AS last_seen
            FROM events
            GROUP BY user_id
        )
        SELECT
            *,
            CASE
                WHEN total_purchases = 0 THEN 'Browser'
                WHEN total_purchases = 1 THEN 'One-time Buyer'
                WHEN total_purchases >= 2 AND total_spend < 100 THEN 'Repeat Buyer'
                WHEN total_purchases >= 2 AND total_spend >= 100 THEN 'High-Value Buyer'
                ELSE 'Other'
            END AS segment,
            CASE
                WHEN total_sessions >= 10 THEN 'Power User'
                WHEN total_sessions >= 3 THEN 'Regular'
                ELSE 'Casual'
            END AS frequency_tier
        FROM user_stats
    """, "user_segments")


def generate_product_performance(con):
    save_table(con, """
        SELECT
            product_id,
            category_code,
            category_main,
            brand,
            COUNT(*) FILTER (WHERE event_type='view') AS views,
            COUNT(*) FILTER (WHERE event_type='cart') AS carts,
            COUNT(*) FILTER (WHERE event_type='purchase') AS purchases,
            COALESCE(SUM(price) FILTER (WHERE event_type='purchase'), 0) AS revenue,
            COALESCE(AVG(price), 0) AS avg_price,
            CASE WHEN views > 0 THEN ROUND(100.0 * purchases / views, 3) ELSE 0 END AS conversion_rate
        FROM events
        GROUP BY product_id, category_code, category_main, brand
        ORDER BY revenue DESC
    """, "product_performance")


def generate_hourly_patterns(con):
    save_table(con, """
        SELECT
            EXTRACT('dow' FROM event_time) AS day_of_week,
            EXTRACT('hour' FROM event_time) AS hour_of_day,
            COUNT(*) FILTER (WHERE event_type='view') AS views,
            COUNT(*) FILTER (WHERE event_type='cart') AS carts,
            COUNT(*) FILTER (WHERE event_type='purchase') AS purchases,
            COALESCE(SUM(price) FILTER (WHERE event_type='purchase'), 0) AS revenue
        FROM events
        GROUP BY day_of_week, hour_of_day
        ORDER BY day_of_week, hour_of_day
    """, "hourly_patterns")


# ───────────────────────────────────────────────────────────────────────────────
# FILTER CATALOG
# ───────────────────────────────────────────────────────────────────────────────
def generate_filter_catalog(con):
    """Generate static filter lookup tables for the frontend."""
    log("Generating filter catalog...")

    # Categories
    out = os.path.join(ANALYTICS_DIR, "filter_categories.parquet")
    con.execute(f"""
        COPY (
            SELECT DISTINCT category_main AS value, COUNT(*) AS event_count
            FROM events
            WHERE category_main != 'unknown' AND category_main != ''
            GROUP BY category_main
            ORDER BY event_count DESC
            LIMIT 100
        ) TO '{out}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """)

    # Brands
    out = os.path.join(ANALYTICS_DIR, "filter_brands.parquet")
    con.execute(f"""
        COPY (
            SELECT DISTINCT brand AS value, COUNT(*) AS event_count
            FROM events
            WHERE brand != 'unknown' AND brand != ''
            GROUP BY brand
            ORDER BY event_count DESC
            LIMIT 200
        ) TO '{out}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """)

    log("  ✓ filter catalogs saved")


# ───────────────────────────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────────────────────────
def main():
    total_start = time.time()
    log("=" * 60)
    log("Product Analytics Dashboard — Preprocessing Pipeline")
    log(f"Data source: {CSV_GLOB}")
    log(f"Output dir:  {ANALYTICS_DIR}")
    log("=" * 60)

    con = get_connection()
    create_events_view(con)

    log("\nGenerating analytics tables...")
    generate_daily_active_users(con)
    generate_weekly_active_users(con)
    generate_session_summary(con)    # tiny single-row KPI table — read by /api/behavior
    generate_session_metrics(con)    # large raw-session table — retained for advanced queries
    generate_funnel_metrics(con)
    generate_revenue_metrics(con)
    generate_category_performance(con)
    generate_brand_performance(con)
    generate_retention_cohorts(con)
    generate_user_segments(con)
    generate_product_performance(con)
    generate_hourly_patterns(con)
    generate_filter_catalog(con)

    log("\n" + "=" * 60)
    log(f"Pipeline complete in {time.time()-total_start:.1f}s")
    log(f"Output tables: {ANALYTICS_DIR}")
    log("=" * 60)

    con.close()


if __name__ == "__main__":
    main()
