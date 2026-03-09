"""
FastAPI — Retention Cohort Analysis endpoint.
"""

from fastapi import APIRouter, Query
from typing import Optional
from db import query, table

router = APIRouter(prefix="/api/retention", tags=["retention"])


@router.get("")
def get_retention():
    ret_tbl = table("retention_cohorts")

    # Full cohort matrix for heatmap
    cohort_matrix = query(f"""
        SELECT
            cohort_week::TEXT AS cohort_week,
            activity_week::TEXT AS activity_week,
            cohort_size,
            retained_users,
            retention_pct,
            week_number
        FROM {ret_tbl}
        WHERE week_number <= 8
        ORDER BY cohort_week, week_number
    """)

    # Summary: retention by week number (avg across all cohorts)
    week_averages = query(f"""
        SELECT
            week_number,
            ROUND(AVG(retention_pct), 2) AS avg_retention_pct,
            SUM(retained_users) AS total_retained
        FROM {ret_tbl}
        WHERE week_number <= 8
        GROUP BY week_number
        ORDER BY week_number
    """)

    return {
        "cohort_matrix": cohort_matrix,
        "week_averages": week_averages,
    }
