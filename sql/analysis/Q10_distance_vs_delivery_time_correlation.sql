-- =============================================================================
-- Q10 — Does distance correlate with delivery time, or is it condition-driven?
-- Priority: P1 | SQL_ANALYSIS_PLAN.md
--
-- Filtered to coordinates_valid_flag = true only (Cleaning Step 7) — an
-- invalid coordinate produces no distance_km value at all (NULL, per
-- FEATURE_ENGINEERING.md #1), so this filter is required for CORR() to
-- run on a meaningful population; the row count used is reported
-- explicitly, per SQL_ANALYSIS_PLAN.md's validation method for Q10.
--
-- CORR() is a descriptive statistic (Pearson r), not a hypothesis test —
-- the formal test lives in STATISTICAL_ANALYSIS.md Test 4 (Python Phase 2).
-- =============================================================================

SET search_path TO routeiq, public;

-- Distance vs delivery time correlation (coordinate-valid rows only)
SELECT
    COUNT(*) AS n_coordinate_valid_rows,
    ROUND(CORR(f.distance_km, f.delivery_time_minutes)::numeric, 4) AS pearson_r
FROM routeiq."FactDelivery" f
WHERE f.coordinates_valid_flag = TRUE;

-- Comparison view: average distance and delivery time by weather/traffic
-- condition — lets a reader compare whether condition (weather/traffic)
-- or distance better explains delivery-time variation, per Q10's framing.
SELECT
    wt.weather,
    wt.traffic,
    COUNT(*) FILTER (WHERE f.coordinates_valid_flag) AS n_coordinate_valid,
    ROUND(AVG(f.distance_km) FILTER (WHERE f.coordinates_valid_flag)::numeric, 2) AS avg_distance_km,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes
FROM routeiq."FactDelivery" f
JOIN routeiq."DimWeatherTraffic" wt ON wt.weather_traffic_key = f.weather_traffic_key
GROUP BY wt.weather, wt.traffic
ORDER BY avg_delivery_time_minutes DESC;
