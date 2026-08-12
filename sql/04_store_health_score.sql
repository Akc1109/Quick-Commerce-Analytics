-- ============================================
-- COMBINED STORE HEALTH SCORE
-- Blends SLA breach rate + inventory mismatch severity into one ranking
-- ============================================

WITH sla_perf AS (
    SELECT
        store_id,
        ROUND(
            100.0 * SUM(CASE WHEN actual_delivery_time > promised_delivery_time THEN 1 ELSE 0 END) / COUNT(*),
            2
        ) AS breach_rate_pct
    FROM orders
    GROUP BY store_id
),
supply AS (
    SELECT store_id, product_id, SUM(quantity) AS total_stocked
    FROM inventory_stock
    GROUP BY store_id, product_id
),
demand AS (
    SELECT o.store_id, oi.product_id, SUM(oi.quantity) AS total_sold
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    GROUP BY o.store_id, oi.product_id
),
mismatch AS (
    SELECT
        s.store_id,
        s.product_id,
        ABS(
            100.0 * (s.total_stocked - COALESCE(d.total_sold, 0)) / NULLIF(s.total_stocked, 0)
        ) AS abs_mismatch_pct
    FROM supply s
    LEFT JOIN demand d ON s.store_id = d.store_id AND s.product_id = d.product_id
),
inventory_perf AS (
    SELECT
        store_id,
        ROUND(AVG(abs_mismatch_pct), 2) AS avg_mismatch_pct
    FROM mismatch
    GROUP BY store_id
)
SELECT
    sla.store_id,
    sla.breach_rate_pct,
    inv.avg_mismatch_pct,
    ROUND((sla.breach_rate_pct + inv.avg_mismatch_pct) / 2, 2) AS health_score_penalty
FROM sla_perf sla
JOIN inventory_perf inv ON sla.store_id = inv.store_id
ORDER BY health_score_penalty DESC;