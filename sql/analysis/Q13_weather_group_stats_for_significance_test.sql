-- =============================================================================
-- Q13 — Is weather statistically significant for delivery time? (group-stats prep)
-- Priority: P1 | SQL_ANALYSIS_PLAN.md
--
-- SCOPE BOUNDARY: identical to Q03 — this produces the group inputs for
-- STATISTICAL_ANALYSIS.md Test 2 (ANOVA / Kruskal-Wallis). No p-value or
-- test statistic is computed in SQL.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    wt.weather,
    COUNT(*) AS n,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
    ROUND(STDDEV(f.delivery_time_minutes)::numeric, 2) AS stddev_delivery_time_minutes,
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.delivery_time_minutes)::numeric,
        2
    ) AS median_delivery_time_minutes
FROM routeiq."FactDelivery" f
JOIN routeiq."DimWeatherTraffic" wt ON wt.weather_traffic_key = f.weather_traffic_key
GROUP BY wt.weather
ORDER BY avg_delivery_time_minutes DESC;
