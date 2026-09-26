-- =============================================================================
-- Q20 — Area + traffic combination with highest breach concentration
-- Priority: P1 | SQL_ANALYSIS_PLAN.md
--
-- KPI: Delay Root-Cause Share / Pareto Concentration (KPI_DEFINITIONS.md #7),
-- 2-D cut (area x traffic) — this is the combined cut DASHBOARD_PLANNING.md
-- Page 4's Pareto chart is built from.
--
-- MINIMUM SAMPLE SIZE (see reports/sql_analysis_preflight.md policy):
-- SQL_ANALYSIS_PLAN.md asks for low-count combinations to be "flagged/
-- excluded" but no numeric threshold is frozen anywhere in the
-- documentation. row_count is exposed as a visible column instead of an
-- invented cutoff, so low-count combinations are visible, not silently
-- equal-weighted with high-count ones, without fabricating a policy.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    a.area_name,
    a.area_tier_valid_flag,
    wt.traffic,
    COUNT(*) AS row_count,
    COUNT(*) FILTER (WHERE f.sla_breach_flag) AS breach_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.sla_breach_flag) / COUNT(*), 4) AS breach_rate_pct
FROM routeiq."FactDelivery" f
JOIN routeiq."DimArea" a ON a.area_key = f.area_key
JOIN routeiq."DimWeatherTraffic" wt ON wt.weather_traffic_key = f.weather_traffic_key
GROUP BY a.area_name, a.area_tier_valid_flag, wt.traffic
ORDER BY breach_count DESC;
