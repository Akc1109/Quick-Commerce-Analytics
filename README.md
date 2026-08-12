# Quick Commerce Ops Analytics: Dark Store Optimization & SLA Breach Analysis

I built this project to simulate the backend operations of a 10-minute delivery platform (think Blinkit or Zepto) and dig into two questions any ops team at one of these companies would actually care about:

1. Why are deliveries missing their promised delivery time, and where is it worst?
2. Are the dark stores stocking the right products in the right amounts?

It covers the whole pipeline myself, end to end — I generated the data in Python, designed and queried the database in PostgreSQL, and built the dashboard in Power BI.

## Why I built it this way

I didn't want to just download a Kaggle dataset and make another "sales by region" dashboard — every portfolio has one of those. So I generated my own data instead, and specifically built causal patterns into it (traffic causing delays, demand mismatches causing stockouts) rather than pure randomness, so there'd actually be something real for the SQL to uncover.

I also picked an ops angle instead of a sales/marketing one, since delivery SLAs and dark store logistics are a live, current problem for these companies, not just a generic retail metric.

---

## Tech stack

| Layer | Tool |
|---|---|
| Data generation | Python (pandas, numpy, Faker) |
| Database | PostgreSQL |
| Data loading | SQLAlchemy |
| Analysis | SQL (CTEs, window functions, multi-table joins) |
| Visualization | Power BI (DAX measures, Power Query native SQL queries) |

---

## Project structure

```
quick_commerce_project/
├── python/
│   ├── 01_generate_base_tables.py          # customers, dark_stores, products, riders
│   ├── 02_generate_transactional_data.py   # orders, order_items, inventory_stock, traffic flags
│   └── 03_load_to_postgres.py              # loads all CSVs into Postgres
├── sql/
│   ├── 01_schema.sql                       # 8-table relational schema (DDL)
│   ├── 02_sla_breach_analysis.sql          # breach rate by store, traffic, load
│   ├── 03_inventory_mismatch_analysis.sql  # over/understock analysis
│   └── 04_store_health_score.sql           # combined store ranking
├── data/                                   # generated CSVs (gitignored if large)
└── powerbi/
    └── quick_commerce_dashboard.pbix
```

---

## Data model

8 tables. I trimmed this down a fair bit during design — I'd originally planned to also analyze customer retention and discount cannibalization, but once I narrowed the scope to just ops (SLA + inventory), columns like `acquisition_channel` and `discount_applied` weren't being used by anything, so I cut them rather than leave dead weight in the schema.

- `customers` — customer_id, city
- `dark_stores` — store_id, city, zone, capacity, opening_date
- `products` — product_id, category, shelf_life_days, unit_cost, price
- `riders` — rider_id, store_id, join_date
- `inventory_stock` — restock events per store/product over time
- `orders` — order_time, promised_delivery_time, actual_delivery_time, order_value
- `order_items` — line items per order
- `weather_traffic_flags` — hourly traffic/weather conditions per zone

Scale: 30,000 customers, 18 dark stores across 5 cities, 34 products, 90 days of activity, ~108K orders, ~378K order line items, ~12K restock events.

## How the data was generated

I didn't want random noise, so delivery times are built from a formula: base delay + a fixed baseline efficiency per store + a traffic effect + a weather effect + a concurrent-order-load effect + some random noise on top. That way stores genuinely differ from each other, and traffic/load actually explain some of the variation, instead of everything being a coin flip.

Inventory was the trickier one. My first attempt generated stock quantities independently of actual demand, and it produced a fairly obvious real-world problem: some products showed stores "selling" way more units than were ever stocked, which doesn't make sense and is exactly the kind of thing that'd fall apart under a recruiter's questioning. I fixed it by making restock quantities demand-aware — I calculate what was actually ordered for each store-product combo first, then generate stock as a percentage of that (sometimes over, sometimes under, on purpose), so the mismatches are realistic instead of physically impossible.

Honestly this took a few passes to get right. My first version of the SLA breach logic made every store look almost identical (all clustered around 50-56%), which meant there was no real story for the SQL to find. I tightened it, overshot, and ended up with stores stuck at either ~100% or ~4% breach rate with nothing in between. Third attempt landed on a realistic spread — 6% at the best store up to 84% at the worst, with traffic and load meaningfully explaining the difference.

---

## What I found

**Breach rate is all over the place depending on the store.** Anywhere from 6% at the best store to 84% at the worst, across 18 stores. That alone tells you this isn't a "the whole system is slow" problem — it's specific stores that need attention.

**Traffic explains most of it.**

| Traffic level | Breach rate |
|---|---|
| Low | 12.46% |
| Medium | 27.38% |
| High | 69.11% |

Breach rate is basically 6x higher when traffic is high vs. low. This was the strongest single factor I found, by a wide margin.

**Store congestion matters too, but less than I expected.**

| Concurrent load | Breach rate |
|---|---|
| Low (1-5 orders/hr) | 35.38% |
| Medium (6-12 orders/hr) | 46.24% |
| High (13+ orders/hr) | 48.19% |

There's a real jump from low to medium load, but medium and high are pretty close to each other. So it matters, just not nearly as much as traffic does.

**Inventory mismatch isn't a "one bad category" problem.** I expected maybe one or two product categories to be consistently off, but overstock and understock both show up across almost every category — Bakery, Snacks, Dairy, Beverages, Household, you name it. Some products are off by 40-50% one way or the other, a few worse. The more interesting bit: the exact same product can be overstocked at one store and understocked at another. That's not a demand forecasting problem at the company level, it's inconsistent restocking decisions store-by-store.

**SLA and inventory turned out to be pretty separate problems.** I built a combined "store health score" expecting the worst SLA stores to also be the worst on inventory, but that's not really what happened — inventory mismatch stays fairly consistent across stores while breach rate swings wildly. So these need to be treated as two different fixes, not one root cause.

## So what would I actually do with this

- Traffic is the main lever, not store congestion — so dynamic delivery windows or extra staffing during known high-traffic hours would probably help more than just hiring more riders per store
- Restocking should be driven by actual per-store demand data instead of whatever each store manager decides, since that's clearly what's causing the same product to be over- and understocked in different places
- SLA and inventory should have separate owners/metrics internally, since fixing one won't fix the other

---

## What I'd do next if I kept going

- Pull in real historical weather data instead of simulating it, just to make that part less synthetic
- I generated a `riders` table with join dates but never actually used it for anything — a rider efficiency analysis would be a natural next add-on
- A time-series view of breach rate over the 90 days would probably surface trends the current snapshot-style charts miss

## Dashboard

Two pages in Power BI:
- **SLA Breach Analysis** — breach rate by store, by traffic level, by concurrent load
- **Inventory Health & Store Rankings** — top over/understocked products, plus the combined store health scorecard

(Screenshots go here — exporting from Power BI next.)
