-- =============================================================================
-- Q06 — Categories with highest average delivery time
-- Priority: P2 | SQL_ANALYSIS_PLAN.md
--
-- KPI: Average Delivery Time (KPI_DEFINITIONS.md #3), by Category.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    c.category_name,
    COUNT(*) AS n,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
    ROUND(
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY f.delivery_time_minutes)::numeric,
        2
    ) AS p90_delivery_time_minutes
FROM routeiq."FactDelivery" f
JOIN routeiq."DimCategory" c ON c.category_key = f.category_key
GROUP BY c.category_name
ORDER BY avg_delivery_time_minutes DESC;
