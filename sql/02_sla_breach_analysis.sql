-- ============================================
-- SLA BREACH ANALYSIS
-- ============================================

-- 1. Breach rate by store
SELECT
    store_id,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN actual_delivery_time > promised_delivery_time THEN 1 ELSE 0 END) AS breached_orders,
    ROUND(
        100.0 * SUM(CASE WHEN actual_delivery_time > promised_delivery_time THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS breach_rate_pct
FROM orders
GROUP BY store_id
ORDER BY breach_rate_pct DESC;


-- 2. Breach rate by traffic level
SELECT
    wtf.traffic_level,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN o.actual_delivery_time > o.promised_delivery_time THEN 1 ELSE 0 END) AS breached_orders,
    ROUND(
        100.0 * SUM(CASE WHEN o.actual_delivery_time > o.promised_delivery_time THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS breach_rate_pct
FROM orders o
JOIN dark_stores ds ON o.store_id = ds.store_id
JOIN weather_traffic_flags wtf
    ON wtf.zone = ds.zone
    AND wtf.date = o.order_time::date
    AND wtf.hour = EXTRACT(HOUR FROM o.order_time)
GROUP BY wtf.traffic_level
ORDER BY breach_rate_pct DESC;


-- 3. Breach rate by concurrent store load
WITH store_hour_load AS (
    SELECT
        store_id,
        order_time::date AS order_date,
        EXTRACT(HOUR FROM order_time) AS order_hour,
        COUNT(*) AS concurrent_orders
    FROM orders
    GROUP BY store_id, order_time::date, EXTRACT(HOUR FROM order_time)
),
orders_with_load AS (
    SELECT
        o.*,
        shl.concurrent_orders,
        CASE
            WHEN shl.concurrent_orders <= 5 THEN 'Low (1-5)'
            WHEN shl.concurrent_orders <= 12 THEN 'Medium (6-12)'
            ELSE 'High (13+)'
        END AS load_bucket
    FROM orders o
    JOIN store_hour_load shl
        ON o.store_id = shl.store_id
        AND o.order_time::date = shl.order_date
        AND EXTRACT(HOUR FROM o.order_time) = shl.order_hour
)
SELECT
    load_bucket,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN actual_delivery_time > promised_delivery_time THEN 1 ELSE 0 END) AS breached_orders,
    ROUND(
        100.0 * SUM(CASE WHEN actual_delivery_time > promised_delivery_time THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS breach_rate_pct
FROM orders_with_load
GROUP BY load_bucket
ORDER BY breach_rate_pct DESC;