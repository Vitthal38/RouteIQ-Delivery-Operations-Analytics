-- =============================================================================
-- Q03 — Does traffic significantly affect delivery time? (group-stats prep)
-- Priority: P1 | SQL_ANALYSIS_PLAN.md
--
-- SCOPE BOUNDARY: this query produces the group means/variances/counts
-- that STATISTICAL_ANALYSIS.md Test 1 (ANOVA / Kruskal-Wallis) consumes.
-- The significance test itself — p-value, assumption checks, effect size
-- — is explicitly Python Phase 2 work, out of scope for this SQL phase.
-- No p-value or test statistic is computed anywhere in this file.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    wt.traffic,
    COUNT(*) AS n,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
    ROUND(STDDEV(f.delivery_time_minutes)::numeric, 2) AS stddev_delivery_time_minutes,
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.delivery_time_minutes)::numeric,
        2
    ) AS median_delivery_time_minutes
FROM routeiq."FactDelivery" f
JOIN routeiq."DimWeatherTraffic" wt ON wt.weather_traffic_key = f.weather_traffic_key
GROUP BY wt.traffic
ORDER BY avg_delivery_time_minutes DESC;
