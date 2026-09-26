-- =============================================================================
-- Q21 — Does vehicle type affect average delivery time?
-- Priority: P2 | SQL_ANALYSIS_PLAN.md
--
-- KNOWN LIMITATION (Phase 2 finding, approved before this phase began):
-- DimVehicle contains only 3 members (motorcycle, scooter, van). The raw
-- dataset's 4th vehicle type, bicycle (15 rows), is NOT present in the
-- cleaned/loaded FactDelivery at all — all 15 raw bicycle rows fell inside
-- the Cleaning Step 3 91-row exclusion cluster (missing Weather/Traffic).
-- This question therefore cannot be answered for bicycle under any
-- confidence level; it is not merely low-confidence as
-- SQL_ANALYSIS_PLAN.md's original note anticipated ("bicycle has only 15
-- rows... flagged as low-confidence"). No bicycle row is fabricated or
-- reintroduced here — the query simply reflects the 3 vehicle types that
-- actually exist in the approved dataset.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    v.vehicle_name,
    COUNT(*) AS n,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
    ROUND(
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY f.delivery_time_minutes)::numeric,
        2
    ) AS p90_delivery_time_minutes
FROM routeiq."FactDelivery" f
JOIN routeiq."DimVehicle" v ON v.vehicle_key = f.vehicle_key
GROUP BY v.vehicle_name
ORDER BY avg_delivery_time_minutes DESC;
