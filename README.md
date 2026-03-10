# E-commerce Product Analytics Platform

A full-stack product analytics platform that turns raw e-commerce event logs into business decisions — covering funnel health, cohort retention, user segmentation, revenue concentration, and A/B test results.

---

**Live Demo:** [e-commerce-product-analytics.vercel.app](https://e-commerce-product-analytics.vercel.app)  
**GitHub:** [github.com/AdarshBennur/E-commerce-ProductAnalytics](https://github.com/AdarshBennur/E-commerce-ProductAnalytics)

---

## Product Overview

E-commerce teams generate enormous amounts of behavioral data but rarely have a single place to answer the questions that matter: *Where are users dropping off? Which cohort is churning fastest? Which category owns all the revenue?* This platform answers those questions in one dashboard, without a data team needing to write SQL every time a product manager asks.

In a real company, this would sit between the data warehouse and the product team — used daily by growth analysts, product managers, and marketing leads to prioritise roadmap bets, evaluate experiments, and identify revenue risks before they compound.

---

## Analytics & Metrics Layer

### Executive Overview
Tracks the five core product health metrics on a daily basis: **DAU, sessions, purchases, revenue, and views/carts funnel**. Charts are annotated with statistical spike detection (z-score) so anomalies surface without manual investigation.

| Metric | Value (Nov 2019) |
|---|---|
| Avg Daily Active Users | 3,891 |
| Peak DAU (single day) | 10,745 |
| Total Purchases | 1,376 |
| Total Revenue | $427,763 |
| Session → Purchase CVR | 6.07% |

The overview answers: *Is the product healthy today?*

---

### Funnel Analysis
Tracks the three-stage e-commerce funnel: **view → cart → purchase**, sliced by date, category, and brand.

| Stage | Events | Conversion |
|---|---|---|
| Product Views | 94,150 | — |
| Add-to-Cart | 4,474 | 4.75% view → cart |
| Purchases | 1,376 | 30.76% cart → purchase |

The 4.75% view-to-cart rate signals a product discovery problem — users browse extensively (4.51 product views per session) but rarely commit to cart. The 30.76% cart-to-purchase rate is healthy, meaning checkout is not the primary friction point.

**Decision this drives:** Invest in product page optimisation before checkout.

---

### Retention & Cohorts
Cohorts are defined by the calendar week a user first appeared. Retention is measured as the percentage of that cohort returning in each subsequent week.

| Week | Avg Retention |
|---|---|
| Week 0 (acquisition) | 100% |
| Week 1 | 21.71% |
| Week 2 | 18.46% |
| Week 4 | 18.29% |
| Week 7 | 16.52% |

The drop from week 1 (21.71%) to week 4 (18.29%) is only 3.42pp — atypically gradual for e-commerce — signalling a core segment of moderately loyal return visitors.

**Decision this drives:** Effort is better placed at week 1 activation than mid-funnel re-engagement nudges.

---

### User Behavior
Session-level patterns from 23.1M sessions in the full dataset reveal the dominant usage mode.

| Metric | Value |
|---|---|
| Avg Session Duration | 5.73 min |
| Avg Events per Session | 4.76 |
| Avg Product Views per Session | 4.51 |
| Avg Unique Products Seen | 3.02 |
| Session Conversion Rate | 6.07% |

User segments by purchase history:

| Segment | Users | Avg Spend |
|---|---|---|
| Browser (no purchases) | 4,619,179 (86.6%) | $0 |
| One-time Buyer | 402,145 (7.5%) | $267 |
| High-Value Buyer | 273,273 (5.1%) | $1,450 |
| Repeat Buyer | 22,052 (0.4%) | $65 |

Monday generates the highest purchase volume (353,614 purchases) — a useful signal for flash sale and campaign timing.

**Decision this drives:** 86.6% of users never buy. The gap is converting browsers, not retaining buyers. High-value buyers (5.1% of users, $1,450 avg spend) are the segment most worth protecting.

---

### Category & Revenue Analysis
Revenue is highly concentrated in a single category.

| Category | Revenue | Share |
|---|---|---|
| Electronics | $322,470 | 75.4% |
| Appliances | $26,643 | 6.2% |
| Computers | $22,397 | 5.2% |
| Other | $56,254 | 13.2% |

Within electronics, **smartphones** account for the largest single sub-category ($270,839). Top brands by revenue: Apple ($193,555), Samsung ($84,719), Xiaomi ($18,970).

**Decision this drives:** 75% revenue from one category is a concentration risk. Expanding appliances or computers is a risk-reduction play, not just a growth play.

---

### Experimentation (A/B Testing)
Six experiments modeled across purchase flow, product pages, and re-engagement. Statistical significance is measured by confidence level; lift is calculated as `(variant_cvr − control_cvr) / control_cvr`.

| Experiment | Metric | Control | Variant | Lift | Confidence |
|---|---|---|---|---|---|
| Checkout Flow Simplification | Purchase CVR | 3.2% | 4.7% | +46.9% | 97% ✓ |
| Cart Recovery Email (1h vs 24h) | Recovery Rate | 8.2% | 10.8% | +31.4% | 99% ✓ |
| Free Shipping Progress Bar | AOV | $38.50 | $45.70 | +18.7% | 96% ✓ |
| Urgency Messaging on PDP | Add-to-Cart | 5.8% | 6.3% | +8.6% | 94% ✓ |
| Product Page Image Layout | Add-to-Cart | 6.5% | 7.3% | +12.3% | 82% — |
| Homepage Personalisation | CTR | 12.1% | 12.7% | +5.2% | 61% — |

4 of 6 experiments reached 95%+ confidence. Average observed lift across the portfolio: **+20.5%**.

---

## Key Product Insights Found

| # | Insight | Implication | Recommended Action |
|---|---|---|---|
| 1 | View → cart rate is 4.75% — users view 4.5 products per session but rarely add to cart | Product pages are not converting intent into action | Run PDP tests: social proof, better imagery, clearer pricing |
| 2 | Electronics drives 75.4% of revenue | Single-category dependency is a business risk | Invest in appliance and computer catalog expansion |
| 3 | 86.6% of users never purchase — they only browse | Acquisition is healthy but monetisation is not | Introduce browse-to-buy nudges: wishlist, price drop alerts |
| 4 | High-value buyers (5.1% of users) generate $1,450 avg spend vs $267 for one-time buyers | A small segment disproportionately drives revenue | Build a loyalty program targeting one-time → repeat conversion |
| 5 | Checkout simplification from 4-step to 2-step lifted purchase CVR +46.9% at 97% confidence | Checkout friction is directly measurable and fixable | Ship 2-step checkout to 100% of users — highest-ROI action available |
| 6 | Cart recovery emails sent at 1h outperform 24h by +31.4% at 99% confidence | High-intent cart abandoners convert faster when contacted immediately | Set 1h delay as default for all cart recovery flows |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS, Recharts |
| Backend API | FastAPI (Python), DuckDB |
| Data Storage | Apache Parquet (14 pre-aggregated tables, ~60 MB total) |
| Pipeline | DuckDB SQL, Python (one-time offline preprocessing) |
| Deployment | Vercel (frontend), Render (backend) |

---

## Data Source

**Dataset:** [eCommerce behavior data from multi-category store](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store) — Kaggle  
**Full dataset:** ~285 million rows across 2019-Oct.csv and 2019-Nov.csv (~8.4 GB)  
**Sample used:** 100,000 events from November 2019 (Nov 1 – Nov 25, 2019)  
**Event types:** `view`, `cart`, `purchase`  
**Fields:** timestamp, event type, product ID, category hierarchy, brand, price, user ID, session ID  
**Unique users in sample:** 92,035

The raw CSV is never loaded at runtime. A one-time pipeline aggregates it into 14 Parquet tables that the API reads directly.

---

## Local Setup

```bash
# 1. Install dependencies
cd frontend && npm install
pip install -r backend/requirements.txt

# 2. Run (frontend + backend together)
npm start                      # from repo root

# Frontend only: localhost:3000  |  Backend only: localhost:8000
```

---

## Author

**Adarsh Bennur**  
[adarshbennur.com](https://adarshbennur.com) · [linkedin.com/in/adarshbennur](https://linkedin.com/in/adarshbennur) · [github.com/AdarshBennur](https://github.com/AdarshBennur)
