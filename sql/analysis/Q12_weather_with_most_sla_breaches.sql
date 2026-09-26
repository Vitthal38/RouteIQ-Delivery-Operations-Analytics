-- =============================================================================
-- Q12 — Weather condition with most SLA breaches
-- Priority: P1 | SQL_ANALYSIS_PLAN.md
--
-- KPI: SLA Breach Rate (KPI_DEFINITIONS.md #2), by Weather. Reads the
-- frozen sla_breach_flag as-is.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    wt.weather,
    COUNT(*) AS total_deliveries,
    COUNT(*) FILTER (WHERE f.sla_breach_flag) AS total_breaches,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.sla_breach_flag) / COUNT(*), 4) AS breach_rate_pct
FROM routeiq."FactDelivery" f
JOIN routeiq."DimWeatherTraffic" wt ON wt.weather_traffic_key = f.weather_traffic_key
GROUP BY wt.weather
ORDER BY total_breaches DESC;

-- Reconciliation: sum of per-weather breach counts must equal total breach count
SELECT COUNT(*) FILTER (WHERE sla_breach_flag) AS total_breaches_overall
FROM routeiq."FactDelivery";
