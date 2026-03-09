"""
FastAPI — Category & Brand Performance endpoint.
"""

from fastapi import APIRouter, Query
from typing import Optional
from db import query, table

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
def get_categories(
    limit: int = Query(15),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    cat_tbl = table("category_performance")
    brand_tbl = table("brand_performance")

    # We use the precomputed totals (no date filtering needed for category perf table,
    # date-filtered version comes from revenue_metrics if needed)

    # Top categories by revenue
    top_categories = query(f"""
        SELECT
            category_main AS category,
            SUM(views) AS views,
            SUM(carts) AS carts,
            SUM(purchases) AS purchases,
            ROUND(SUM(revenue), 2) AS revenue,
            ROUND(AVG(avg_price), 2) AS avg_price,
            ROUND(AVG(conversion_rate), 3) AS conversion_rate
        FROM {cat_tbl}
        WHERE category_main != 'unknown' AND category_main != ''
        GROUP BY category_main
        ORDER BY revenue DESC
        LIMIT {limit}
    """)

    # Top brands by revenue
    top_brands = query(f"""
        SELECT
            brand,
            views,
            carts,
            purchases,
            ROUND(revenue, 2) AS revenue,
            ROUND(avg_price, 2) AS avg_price,
            ROUND(conversion_rate, 3) AS conversion_rate
        FROM {brand_tbl}
        WHERE brand != 'unknown' AND brand != ''
        ORDER BY revenue DESC
        LIMIT {limit}
    """)

    # Category conversion rates (for comparison chart)
    category_conversion = query(f"""
        SELECT
            category_main AS category,
            ROUND(SUM(purchases)::FLOAT / NULLIF(SUM(views), 0) * 100, 3) AS conversion_rate,
            SUM(views) AS views,
            SUM(purchases) AS purchases
        FROM {cat_tbl}
        WHERE category_main != 'unknown' AND category_main != ''
        GROUP BY category_main
        HAVING SUM(views) > 1000
        ORDER BY conversion_rate DESC
        LIMIT {limit}
    """)

    return {
        "top_categories": top_categories,
        "top_brands": top_brands,
        "category_conversion": category_conversion,
    }
