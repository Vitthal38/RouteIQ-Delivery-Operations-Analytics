-- =============================================================================
-- Q19 — Delivery-time delta: clear vs. adverse weather
-- Priority: P1 | SQL_ANALYSIS_PLAN.md
--
-- GROUP DEFINITION (stated explicitly, per the plan's own requirement —
-- "must be explicitly defined... documented in the query comment, not
-- left ambiguous"): "Clear" = Weather = 'Sunny'. "Adverse" = all other
-- observed Weather values (Cloudy, Fog, Sandstorms, Stormy, Windy) —
-- exactly the plan's own suggested example ("e.g., all non-Sunny
-- categories"). This is also the grouping STATISTICAL_ANALYSIS.md Test 2
-- uses for its secondary two-group comparison.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    CASE WHEN wt.weather = 'Sunny' THEN 'Clear (Sunny)' ELSE 'Adverse (non-Sunny)' END AS weather_group,
    COUNT(*) AS n,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
    ROUND(
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY f.delivery_time_minutes)::numeric,
        2
    ) AS p90_delivery_time_minutes
FROM routeiq."FactDelivery" f
JOIN routeiq."DimWeatherTraffic" wt ON wt.weather_traffic_key = f.weather_traffic_key
GROUP BY weather_group
ORDER BY weather_group;
