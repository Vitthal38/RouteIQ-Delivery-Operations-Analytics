-- =============================================================================
-- Q08 — OTD% by area
-- Priority: P0 | SQL_ANALYSIS_PLAN.md
--
-- KPI: On-Time Delivery Rate % (KPI_DEFINITIONS.md #1), by area. Inverse
-- framing of Q01 — OTD% + Breach% must sum to 100 for every area, checked
-- explicitly below (mirrors the DAX_MEASURE_PLAN.md cross-validation rule).
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    a.area_name,
    a.area_tier_valid_flag,
    COUNT(*) AS total_deliveries,
    COUNT(*) FILTER (WHERE NOT f.sla_breach_flag) AS on_time_deliveries,
    ROUND(100.0 * COUNT(*) FILTER (WHERE NOT f.sla_breach_flag) / COUNT(*), 4) AS otd_rate_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.sla_breach_flag) / COUNT(*), 4) AS breach_rate_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE NOT f.sla_breach_flag) / COUNT(*), 4)
        + ROUND(100.0 * COUNT(*) FILTER (WHERE f.sla_breach_flag) / COUNT(*), 4) AS otd_plus_breach_check
FROM routeiq."FactDelivery" f
JOIN routeiq."DimArea" a ON a.area_key = f.area_key
GROUP BY a.area_name, a.area_tier_valid_flag
ORDER BY otd_rate_pct ASC;
