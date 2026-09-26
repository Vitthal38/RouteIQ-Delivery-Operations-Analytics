-- =============================================================================
-- Q01 — % of deliveries breaching SLA overall and by area
-- Priority: P0 | SQL_ANALYSIS_PLAN.md
--
-- KPI: SLA Breach Rate (KPI_DEFINITIONS.md #2). Reads the frozen
-- FactDelivery.sla_breach_flag as-is — no threshold or percentile is
-- recalculated here.
--
-- Area-tier note: "Other" is retained and shown, not silently dropped
-- (DATA_CLEANING_PLAN.md Step 8). area_tier_valid_flag is exposed so a
-- consumer can filter it out of a strict Urban/Metropolitan/Semi-Urban
-- tier comparison without the row disappearing from this output.
-- =============================================================================

SET search_path TO routeiq, public;

-- Overall breach rate (no grouping)
SELECT
    COUNT(*) AS total_deliveries,
    COUNT(*) FILTER (WHERE f.sla_breach_flag) AS total_breaches,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.sla_breach_flag) / COUNT(*), 4) AS sla_breach_rate_pct
FROM routeiq."FactDelivery" f;

-- Breach rate by area
SELECT
    a.area_name,
    a.area_tier_valid_flag,
    COUNT(*) AS total_deliveries,
    COUNT(*) FILTER (WHERE f.sla_breach_flag) AS total_breaches,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.sla_breach_flag) / COUNT(*), 4) AS sla_breach_rate_pct
FROM routeiq."FactDelivery" f
JOIN routeiq."DimArea" a ON a.area_key = f.area_key
GROUP BY a.area_name, a.area_tier_valid_flag
ORDER BY sla_breach_rate_pct DESC;
