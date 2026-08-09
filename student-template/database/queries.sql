SELECT
    customer_id,
    SUM(total_amount) AS total_order_value
FROM orders
WHERE order_date >= '2025-01-01'
  AND order_date < '2026-01-01'
GROUP BY customer_id
ORDER BY total_order_value DESC
LIMIT 5;
