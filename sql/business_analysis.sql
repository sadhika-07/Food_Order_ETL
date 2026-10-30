USE food_orders_analytics_db;

-- Copy the run_id printed by elt_batch_pipeline.py or shown in its report.
SET @run_id = 'PASTE_RUN_ID_HERE';

-- Total and average order value; NULL values are excluded and counted.
SELECT COUNT(order_value) AS records_included, SUM(order_value) AS total_order_value, AVG(order_value) AS average_order_value
FROM cleaned_food_orders
WHERE source_run_id = @run_id;

-- Highest-count known payment method.
SELECT payment_method, COUNT(*) AS order_count
FROM cleaned_food_orders
WHERE source_run_id = @run_id AND payment_method <> 'Unknown'
GROUP BY payment_method
ORDER BY order_count DESC
LIMIT 1;

-- Channel with most orders.
SELECT order_channel, COUNT(*) AS order_count
FROM cleaned_food_orders
WHERE source_run_id = @run_id
GROUP BY order_channel
ORDER BY order_count DESC
LIMIT 1;

-- Average delivery time for this run.
SELECT COUNT(delivery_time_minutes) AS records_included, AVG(delivery_time_minutes) AS average_delivery_time_minutes
FROM cleaned_food_orders
WHERE source_run_id = @run_id;

-- Simplified assignment formula; COUNT and SUM ignore NULL values.
SELECT COUNT(platform_net_revenue) AS records_included, SUM(platform_net_revenue) AS total_platform_net_revenue
FROM cleaned_food_orders
WHERE source_run_id = @run_id;
