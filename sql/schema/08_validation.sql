-- =============================================================================
-- 08_validation.sql — RouteIQ Phase 2
-- Runs every validation check required for the Phase 2 gate: table/row/column
-- inventory, PK/FK/orphan/duplicate checks, SLA reference and breach-flag
-- validation, source-to-fact reconciliation, dimension cardinality, and
-- index inventory. Every query returns real output — nothing here is a
-- syntactic "should pass" assertion without a result to inspect.
--
-- Run as: psql -U postgres -f 08_validation.sql
-- (Run only after 06_load_dimensions.sql and 07_load_fact.sql have completed.)
-- =============================================================================

SET search_path TO routeiq, public;

\echo '=== 1. TABLE INVENTORY ==='
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'routeiq'
ORDER BY table_name;

\echo '=== 2. ROW COUNTS ==='
SELECT 'DimAgent' AS table_name, COUNT(*) AS row_count FROM routeiq."DimAgent"
UNION ALL SELECT 'DimArea', COUNT(*) FROM routeiq."DimArea"
UNION ALL SELECT 'DimCategory', COUNT(*) FROM routeiq."DimCategory"
UNION ALL SELECT 'DimDate', COUNT(*) FROM routeiq."DimDate"
UNION ALL SELECT 'DimVehicle', COUNT(*) FROM routeiq."DimVehicle"
UNION ALL SELECT 'DimWeatherTraffic', COUNT(*) FROM routeiq."DimWeatherTraffic"
UNION ALL SELECT 'FactDelivery', COUNT(*) FROM routeiq."FactDelivery"
ORDER BY table_name;

\echo '=== 3. COLUMN COUNTS ==='
SELECT table_name, COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_schema = 'routeiq'
GROUP BY table_name
ORDER BY table_name;

\echo '=== 4. PRIMARY KEY VALIDATION (one PK per table; 0 duplicate key values) ==='
SELECT tc.table_name, kcu.column_name AS pk_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'routeiq'
ORDER BY tc.table_name;

SELECT 'DimAgent' AS table_name, COUNT(*) - COUNT(DISTINCT agent_key) AS duplicate_pk_values FROM routeiq."DimAgent"
UNION ALL SELECT 'DimArea', COUNT(*) - COUNT(DISTINCT area_key) FROM routeiq."DimArea"
UNION ALL SELECT 'DimCategory', COUNT(*) - COUNT(DISTINCT category_key) FROM routeiq."DimCategory"
UNION ALL SELECT 'DimDate', COUNT(*) - COUNT(DISTINCT date_key) FROM routeiq."DimDate"
UNION ALL SELECT 'DimVehicle', COUNT(*) - COUNT(DISTINCT vehicle_key) FROM routeiq."DimVehicle"
UNION ALL SELECT 'DimWeatherTraffic', COUNT(*) - COUNT(DISTINCT weather_traffic_key) FROM routeiq."DimWeatherTraffic"
UNION ALL SELECT 'FactDelivery', COUNT(*) - COUNT(DISTINCT delivery_key) FROM routeiq."FactDelivery";

\echo '=== 5. FOREIGN KEY INVENTORY ==='
SELECT
    tc.constraint_name,
    kcu.column_name AS fk_column,
    ccu.table_name AS references_table,
    ccu.column_name AS references_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'routeiq'
ORDER BY tc.constraint_name;

\echo '=== 6. ORPHAN CHECKS (expect 0 for every relationship) ==='
SELECT 'FactDelivery -> DimAgent' AS relationship, COUNT(*) AS orphan_rows
FROM routeiq."FactDelivery" f LEFT JOIN routeiq."DimAgent" d ON f.agent_key = d.agent_key
WHERE d.agent_key IS NULL
UNION ALL
SELECT 'FactDelivery -> DimDate', COUNT(*)
FROM routeiq."FactDelivery" f LEFT JOIN routeiq."DimDate" d ON f.date_key = d.date_key
WHERE d.date_key IS NULL
UNION ALL
SELECT 'FactDelivery -> DimArea', COUNT(*)
FROM routeiq."FactDelivery" f LEFT JOIN routeiq."DimArea" d ON f.area_key = d.area_key
WHERE d.area_key IS NULL
UNION ALL
SELECT 'FactDelivery -> DimCategory', COUNT(*)
FROM routeiq."FactDelivery" f LEFT JOIN routeiq."DimCategory" d ON f.category_key = d.category_key
WHERE d.category_key IS NULL
UNION ALL
SELECT 'FactDelivery -> DimWeatherTraffic', COUNT(*)
FROM routeiq."FactDelivery" f LEFT JOIN routeiq."DimWeatherTraffic" d ON f.weather_traffic_key = d.weather_traffic_key
WHERE d.weather_traffic_key IS NULL
UNION ALL
SELECT 'FactDelivery -> DimVehicle', COUNT(*)
FROM routeiq."FactDelivery" f LEFT JOIN routeiq."DimVehicle" d ON f.vehicle_key = d.vehicle_key
WHERE d.vehicle_key IS NULL;

\echo '=== 7. DUPLICATE CHECKS ==='
SELECT 'FactDelivery.order_id' AS check_name, COUNT(*) - COUNT(DISTINCT order_id) AS duplicate_count FROM routeiq."FactDelivery"
UNION ALL SELECT 'DimArea.area_name', COUNT(*) - COUNT(DISTINCT area_name) FROM routeiq."DimArea"
UNION ALL SELECT 'DimCategory.category_name', COUNT(*) - COUNT(DISTINCT category_name) FROM routeiq."DimCategory"
UNION ALL SELECT 'DimVehicle.vehicle_name', COUNT(*) - COUNT(DISTINCT vehicle_name) FROM routeiq."DimVehicle"
UNION ALL SELECT 'DimDate.full_date', COUNT(*) - COUNT(DISTINCT full_date) FROM routeiq."DimDate"
UNION ALL SELECT 'DimWeatherTraffic (weather,traffic)', COUNT(*) - COUNT(DISTINCT (weather, traffic)) FROM routeiq."DimWeatherTraffic"
UNION ALL SELECT 'DimAgent (age,rating), NULLs as equal',
    COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT agent_age, agent_rating FROM routeiq."DimAgent") x)
    FROM routeiq."DimAgent";

\echo '=== 8. SLA REFERENCE VALIDATION ==='
\echo '-- 8a. Category count in staged sla_reference.csv (expect 16)'
SELECT COUNT(*) AS sla_reference_category_count FROM routeiq.stg_sla_reference;

\echo '-- 8b. Every category has exactly one threshold (expect 0 rows returned)'
SELECT "Category", COUNT(*) FROM routeiq.stg_sla_reference GROUP BY "Category" HAVING COUNT(*) <> 1;

\echo '-- 8c. FactDelivery.sla_threshold_minutes vs sla_reference.csv, per category (expect 0 mismatched rows)'
SELECT
    dc.category_name,
    sref.sla_threshold_minutes AS reference_threshold,
    fct.fact_threshold,
    (sref.sla_threshold_minutes IS DISTINCT FROM fct.fact_threshold) AS mismatch
FROM routeiq.stg_sla_reference sref
JOIN routeiq."DimCategory" dc ON dc.category_name = sref."Category"
JOIN (
    SELECT category_key, sla_threshold_minutes AS fact_threshold
    FROM routeiq."FactDelivery"
    GROUP BY category_key, sla_threshold_minutes
) fct ON fct.category_key = dc.category_key
ORDER BY dc.category_name;

\echo '-- 8d. Every category has exactly one distinct threshold value in FactDelivery (expect 0 rows)'
SELECT category_key, COUNT(DISTINCT sla_threshold_minutes) AS distinct_thresholds
FROM routeiq."FactDelivery"
GROUP BY category_key
HAVING COUNT(DISTINCT sla_threshold_minutes) <> 1;

\echo '-- 8e. No FactDelivery row lacks an SLA threshold (expect 0)'
SELECT COUNT(*) AS rows_missing_threshold FROM routeiq."FactDelivery" WHERE sla_threshold_minutes IS NULL;

\echo '=== 9. SLA BREACH VALIDATION ==='
\echo '-- 9a. sla_breach_flag mismatches vs independent recomputation (expect 0)'
SELECT COUNT(*) AS breach_flag_mismatches
FROM routeiq."FactDelivery"
WHERE sla_breach_flag IS DISTINCT FROM (delivery_time_minutes > sla_threshold_minutes);

\echo '-- 9b. Boundary rule: delivery_time_minutes = sla_threshold_minutes must mean NOT breached'
SELECT
    COUNT(*) AS boundary_row_count,
    COUNT(*) FILTER (WHERE sla_breach_flag) AS incorrectly_flagged_as_breach
FROM routeiq."FactDelivery"
WHERE delivery_time_minutes = sla_threshold_minutes;

\echo '-- 9c. Total breach count and overall breach rate'
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE sla_breach_flag) AS total_breaches,
    ROUND(100.0 * COUNT(*) FILTER (WHERE sla_breach_flag) / COUNT(*), 4) AS breach_rate_pct
FROM routeiq."FactDelivery";

\echo '=== 10. SOURCE-TO-FACT RECONCILIATION ==='
\echo '-- 10a. Row counts: staged cleaned CSV vs FactDelivery (expect equal)'
SELECT
    (SELECT COUNT(*) FROM routeiq.stg_cleaned_delivery) AS staged_rows,
    (SELECT COUNT(*) FROM routeiq."FactDelivery") AS fact_rows;

\echo '-- 10b. Order_ID uniqueness in FactDelivery'
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT order_id) AS distinct_order_ids FROM routeiq."FactDelivery";

\echo '-- 10c. Every staged Order_ID appears exactly once in FactDelivery (expect 0 missing, 0 extra)'
SELECT
    (SELECT COUNT(*) FROM routeiq.stg_cleaned_delivery s
        WHERE NOT EXISTS (SELECT 1 FROM routeiq."FactDelivery" f WHERE f.order_id = s."Order_ID")) AS missing_from_fact,
    (SELECT COUNT(*) FROM routeiq."FactDelivery" f
        WHERE NOT EXISTS (SELECT 1 FROM routeiq.stg_cleaned_delivery s WHERE s."Order_ID" = f.order_id)) AS extra_in_fact;

\echo '=== 11. DIMENSION CARDINALITY (actual vs expected from Step 1 audit) ==='
SELECT 'DimAgent (distinct age/rating combos)' AS dimension, COUNT(*) AS actual, 444 AS expected FROM routeiq."DimAgent"
UNION ALL SELECT 'DimArea', COUNT(*), 4 FROM routeiq."DimArea"
UNION ALL SELECT 'DimCategory', COUNT(*), 16 FROM routeiq."DimCategory"
UNION ALL SELECT 'DimDate', COUNT(*), 44 FROM routeiq."DimDate"
UNION ALL SELECT 'DimVehicle', COUNT(*), 3 FROM routeiq."DimVehicle"
UNION ALL SELECT 'DimWeatherTraffic', COUNT(*), 24 FROM routeiq."DimWeatherTraffic";

\echo '=== 12. INDEX INVENTORY ==='
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'routeiq'
ORDER BY tablename, indexname;

\echo '=== 13. CHECK CONSTRAINT INVENTORY ==='
SELECT conname AS constraint_name, pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE connamespace = 'routeiq'::regnamespace AND contype = 'c'
ORDER BY conname;

\echo '=== VALIDATION SCRIPT COMPLETE ==='
