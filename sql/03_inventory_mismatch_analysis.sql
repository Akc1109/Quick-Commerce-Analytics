-- ============================================
-- INVENTORY MISMATCH ANALYSIS
-- ============================================

-- 1. Overstocked products (surplus_pct DESC = most overstocked first)
-- 2. Understocked products (change ORDER BY to ASC = most understocked first)
WITH supply AS (
    SELECT
        store_id,
        product_id,
        SUM(quantity) AS total_stocked
    FROM inventory_stock
    GROUP BY store_id, product_id
),
demand AS (
    SELECT
        o.store_id,
        oi.product_id,
        SUM(oi.quantity) AS total_sold
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    GROUP BY o.store_id, oi.product_id
)
SELECT
    s.store_id,
    s.product_id,
    p.product_name,
    p.category,
    s.total_stocked,
    COALESCE(d.total_sold, 0) AS total_sold,
    s.total_stocked - COALESCE(d.total_sold, 0) AS surplus_units,
    ROUND(
        100.0 * (s.total_stocked - COALESCE(d.total_sold, 0)) / NULLIF(s.total_stocked, 0),
        2
    ) AS surplus_pct
FROM supply s
LEFT JOIN demand d ON s.store_id = d.store_id AND s.product_id = d.product_id
JOIN products p ON s.product_id = p.product_id
ORDER BY surplus_pct DESC  -- change to ASC for understock view
LIMIT 20;