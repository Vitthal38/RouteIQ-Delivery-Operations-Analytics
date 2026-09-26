-- =============================================================================
-- _final_test_suite.sql — RouteIQ Phase 3, Step 14
-- Cross-cutting tests that are not specific to any single business
-- question: NULL handling, join fan-out (duplicate) checks, denominator
-- reconciliation, and SLA/KPI consistency. Every one of the 22 business
-- questions was already executed individually (see
-- reports/sql_analysis_validation.md); this suite checks the properties
-- that must hold ACROSS all of them for the results to be trustworthy.
-- =============================================================================

SET search_path TO routeiq, public;

\echo '--- TEST 1: Join fan-out check (each Dim join must not change row count) ---'
SELECT
    (SELECT COUNT(*) FROM routeiq."FactDelivery") AS fact_alone,
    (SELECT COUNT(*) FROM routeiq."FactDelivery" f JOIN routeiq."DimAgent" d ON d.agent_key = f.agent_key) AS joined_agent,
    (SELECT COUNT(*) FROM routeiq."FactDelivery" f JOIN routeiq."DimDate" d ON d.date_key = f.date_key) AS joined_date,
    (SELECT COUNT(*) FROM routeiq."FactDelivery" f JOIN routeiq."DimArea" d ON d.area_key = f.area_key) AS joined_area,
    (SELECT COUNT(*) FROM routeiq."FactDelivery" f JOIN routeiq."DimCategory" d ON d.category_key = f.category_key) AS joined_category,
    (SELECT COUNT(*) FROM routeiq."FactDelivery" f JOIN routeiq."DimWeatherTraffic" d ON d.weather_traffic_key = f.weather_traffic_key) AS joined_weather_traffic,
    (SELECT COUNT(*) FROM routeiq."FactDelivery" f JOIN routeiq."DimVehicle" d ON d.vehicle_key = f.vehicle_key) AS joined_vehicle;

\echo '--- TEST 2: NULL handling — agent_rating validity filter excludes exactly 54 rows ---'
SELECT
    (SELECT COUNT(*) FROM routeiq."FactDelivery") AS total_rows,
    (SELECT COUNT(*) FROM routeiq."FactDelivery" f JOIN routeiq."DimAgent" a ON a.agent_key = f.agent_key
        WHERE a.agent_rating_valid_flag = TRUE) AS rating_valid_rows,
    (SELECT COUNT(*) FROM routeiq."FactDelivery" f JOIN routeiq."DimAgent" a ON a.agent_key = f.agent_key
        WHERE a.agent_rating_valid_flag = FALSE) AS rating_invalid_rows,
    (SELECT COUNT(*) FROM routeiq."FactDelivery" WHERE NOT agent_rating_available_flag) AS true_null_rating_rows;

\echo '--- TEST 3: Denominator reconciliation — every group-by cut sums to 43,648 ---'
SELECT 'by area' AS cut, SUM(cnt) AS total FROM (
    SELECT COUNT(*) AS cnt FROM routeiq."FactDelivery" f JOIN routeiq."DimArea" a ON a.area_key = f.area_key GROUP BY a.area_name
) s
UNION ALL
SELECT 'by category', SUM(cnt) FROM (
    SELECT COUNT(*) AS cnt FROM routeiq."FactDelivery" f JOIN routeiq."DimCategory" c ON c.category_key = f.category_key GROUP BY c.category_name
) s
UNION ALL
SELECT 'by vehicle', SUM(cnt) FROM (
    SELECT COUNT(*) AS cnt FROM routeiq."FactDelivery" f JOIN routeiq."DimVehicle" v ON v.vehicle_key = f.vehicle_key GROUP BY v.vehicle_name
) s
UNION ALL
SELECT 'by weather', SUM(cnt) FROM (
    SELECT COUNT(*) AS cnt FROM routeiq."FactDelivery" f JOIN routeiq."DimWeatherTraffic" w ON w.weather_traffic_key = f.weather_traffic_key GROUP BY w.weather
) s
UNION ALL
SELECT 'by traffic', SUM(cnt) FROM (
    SELECT COUNT(*) AS cnt FROM routeiq."FactDelivery" f JOIN routeiq."DimWeatherTraffic" w ON w.weather_traffic_key = f.weather_traffic_key GROUP BY w.traffic
) s
UNION ALL
SELECT 'by weekend/weekday', SUM(cnt) FROM (
    SELECT COUNT(*) AS cnt FROM routeiq."FactDelivery" GROUP BY is_weekend
) s;

\echo '--- TEST 4: SLA consistency — sla_breach_flag re-derived fresh, compared to stored (expect 0 mismatches) ---'
SELECT COUNT(*) AS mismatches
FROM routeiq."FactDelivery"
WHERE sla_breach_flag IS DISTINCT FROM (delivery_time_minutes > sla_threshold_minutes);

\echo '--- TEST 5: KPI consistency — OTD% + Breach% = 100 at 3 filter contexts (no filter, one area, one category) ---'
SELECT 'no filter' AS context,
    ROUND(100.0 * COUNT(*) FILTER (WHERE NOT sla_breach_flag) / COUNT(*), 4) AS otd_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE sla_breach_flag) / COUNT(*), 4) AS breach_pct
FROM routeiq."FactDelivery"
UNION ALL
SELECT 'area = Urban',
    ROUND(100.0 * COUNT(*) FILTER (WHERE NOT f.sla_breach_flag) / COUNT(*), 4),
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.sla_breach_flag) / COUNT(*), 4)
FROM routeiq."FactDelivery" f JOIN routeiq."DimArea" a ON a.area_key = f.area_key WHERE a.area_name = 'Urban'
UNION ALL
SELECT 'category = Grocery',
    ROUND(100.0 * COUNT(*) FILTER (WHERE NOT f.sla_breach_flag) / COUNT(*), 4),
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.sla_breach_flag) / COUNT(*), 4)
FROM routeiq."FactDelivery" f JOIN routeiq."DimCategory" c ON c.category_key = f.category_key WHERE c.category_name = 'Grocery';

\echo '--- TEST 6: Row-count reconciliation vs. Phase 1/Phase 2 frozen figure ---'
SELECT
    (SELECT COUNT(*) FROM routeiq."FactDelivery") AS fact_row_count,
    43648 AS expected_row_count,
    (SELECT COUNT(*) FROM routeiq."FactDelivery") = 43648 AS matches;

\echo '--- TEST 7: Duplicate order_id check (must be 0) ---'
SELECT COUNT(*) - COUNT(DISTINCT order_id) AS duplicate_order_ids FROM routeiq."FactDelivery";

\echo '--- TEST SUITE COMPLETE ---'
