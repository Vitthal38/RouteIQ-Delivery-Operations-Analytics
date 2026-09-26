-- =============================================================================
-- Q05 — Top weather/traffic condition for longest delivery times
-- Priority: P1 | SQL_ANALYSIS_PLAN.md
--
-- KPI: Delivery Time by Weather/Traffic Condition (KPI_DEFINITIONS.md #5),
-- at the combined weather x traffic grain (DimWeatherTraffic).
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    wt.weather,
    wt.traffic,
    COUNT(*) AS n,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
    ROUND(
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY f.delivery_time_minutes)::numeric,
        2
    ) AS p90_delivery_time_minutes,
    RANK() OVER (ORDER BY AVG(f.delivery_time_minutes) DESC) AS avg_time_rank
FROM routeiq."FactDelivery" f
JOIN routeiq."DimWeatherTraffic" wt ON wt.weather_traffic_key = f.weather_traffic_key
GROUP BY wt.weather, wt.traffic
ORDER BY avg_time_rank;
