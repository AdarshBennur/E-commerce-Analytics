# Product Analytics Dashboard

An e-commerce analytics dashboard built with **Next.js** (frontend), **FastAPI** (backend), and **DuckDB** (query engine). All charts and KPIs are served from pre-aggregated Parquet files — the raw dataset is never loaded at runtime.

---

## Architecture

```
data/2019-Nov.csv (9 GB raw)
        │
        ▼  npm run pipeline  (one-time, ~15 s)
        │
data_sample/2019-Nov-sample.csv  (100 K rows, ~13 MB)
        │
        ▼  DuckDB aggregation
        │
analytics/*.parquet  (< 5 MB total, ~200 rows)
        │
        ▼  FastAPI  :8000/api/*
        │
Next.js dashboard  :3000
```

**The dashboard never reads raw CSV files.** Only `analytics/*.parquet` is accessed at runtime.

---

## Quick start

### 1. One-time setup — generate analytics data

Run once after cloning (or whenever you want to refresh the data):

```bash
npm run pipeline
```

This streams `data/2019-Nov.csv` to a 100 K-row sample, then runs DuckDB to produce 5 aggregated Parquet tables in `analytics/`.  Takes ~15 seconds total.

### 2. Start the dashboard (production mode)

```bash
npm start
```

This builds the Next.js frontend once (`next build`) and then starts both servers:

| Server | URL |
|---|---|
| Frontend (Next.js production) | http://localhost:3000 |
| Backend (FastAPI) | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

**Production mode** uses no hot-reload, no webpack watchers, and no dev overlays — RAM usage stays well under 1 GB on the frontend side.

---

## All scripts

| Command | What it does |
|---|---|
| `npm start` | **Main command.** Build frontend → start API + production frontend |
| `npm run build` | Build frontend only (Next.js production build, ~1 GB Node RAM cap) |
| `npm run serve` | Start API + production frontend without rebuilding |
| `npm run api` | Start FastAPI backend only |
| `npm run pipeline` | Generate 100 K-row sample → regenerate analytics Parquet tables |
| `npm run sample` | Regenerate the sample CSV only (streaming, no memory spike) |
| `npm run dev` | Development mode (hot-reload, higher RAM — use only when editing) |

---

## API endpoints

All endpoints return small JSON payloads (aggregated data only).

| Endpoint | Source table |
|---|---|
| `GET /api/overview` | `daily_active_users.parquet` |
| `GET /api/funnel` | `funnel_metrics.parquet` |
| `GET /api/revenue` | `revenue_metrics.parquet` |
| `GET /api/categories` | `category_performance.parquet` + `brand_performance.parquet` |
| `GET /api/retention` | `retention_cohorts.parquet` |
| `GET /api/behavior` | `session_summary.parquet` + `user_segments.parquet` |
| `GET /api/filters` | `filter_categories.parquet` + `filter_brands.parquet` |
| `GET /api/health` | — |

Optional query params on most endpoints: `start_date`, `end_date`, `category`, `brand`.

---

## Memory profile

| Component | RAM usage |
|---|---|
| FastAPI + DuckDB (per query) | < 512 MB (hard limit set) |
| Next.js production server | ~150–250 MB |
| Next.js build step | ~600–800 MB (temporary, during `npm run build`) |
| **Total runtime** | **< 800 MB** |

The 9 GB raw CSV and the 1.3 GB `session_metrics.parquet` are never fully loaded at runtime.

---

## Project structure

```
Dashboard/
├── analytics/          # Pre-aggregated Parquet tables (runtime data source)
├── backend/            # FastAPI application
│   ├── main.py
│   ├── db.py           # DuckDB utilities (512 MB memory limit)
│   └── routers/        # One file per API endpoint
├── data/               # Raw CSV (pipeline input only, never read at runtime)
├── data_sample/        # 100 K-row sample (pipeline intermediate)
├── frontend/           # Next.js application
│   ├── app/            # Pages (overview, funnel, revenue, …)
│   ├── components/     # Shared UI components
│   └── lib/            # API client, types, utilities
└── pipeline/
    ├── create_sample_dataset.py   # Streaming CSV sampler
    └── process_data.py            # DuckDB → Parquet analytics pipeline
```
