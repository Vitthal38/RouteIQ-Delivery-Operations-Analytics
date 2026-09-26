-- =============================================================================
-- Q02 — Worst P90 delivery time by area
-- Priority: P0/P1 | SQL_ANALYSIS_PLAN.md
--
-- KPI: P90 Delivery Time (KPI_DEFINITIONS.md #4), by area.
-- Uses PERCENTILE_CONT(0.90) WITHIN GROUP, matching the exact SQL
-- interpolation method documented in KPI_DEFINITIONS.md #4 and required to
-- match numpy.percentile (Python) / PERCENTILEX.INC (DAX) — the single
-- most likely 3-way mismatch point if this isn't kept consistent.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    a.area_name,
    a.area_tier_valid_flag,
    COUNT(*) AS total_deliveries,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
    ROUND(
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY f.delivery_time_minutes)::numeric,
        2
    ) AS p90_delivery_time_minutes
FROM routeiq."FactDelivery" f
JOIN routeiq."DimArea" a ON a.area_key = f.area_key
GROUP BY a.area_name, a.area_tier_valid_flag
ORDER BY p90_delivery_time_minutes DESC;
