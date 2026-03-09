"""
FastAPI — Filter Catalog endpoint.
Returns available filter values (categories, brands, date bounds).
"""

from fastapi import APIRouter
from db import query, table

router = APIRouter(prefix="/api/filters", tags=["filters"])


@router.get("")
def get_filters():
    cat_tbl = table("filter_categories")
    brand_tbl = table("filter_brands")
    dau_tbl = table("daily_active_users")

    categories = query(f"""
        SELECT value, event_count FROM {cat_tbl}
        ORDER BY event_count DESC
        LIMIT 50
    """)

    brands = query(f"""
        SELECT value, event_count FROM {brand_tbl}
        ORDER BY event_count DESC
        LIMIT 100
    """)

    date_bounds = query(f"""
        SELECT
            MIN(event_date)::TEXT AS min_date,
            MAX(event_date)::TEXT AS max_date
        FROM {dau_tbl}
    """)

    return {
        "categories": [r["value"] for r in categories],
        "brands": [r["value"] for r in brands],
        "date_bounds": date_bounds[0] if date_bounds else {},
    }
