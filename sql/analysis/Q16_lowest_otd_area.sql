-- =============================================================================
-- Q16 — Which area underperforms most on OTD%?
-- Priority: P0 | SQL_ANALYSIS_PLAN.md
--
-- Must equal the minimum value in Q08's own table exactly — this query
-- reuses Q08's identical OTD% computation (not recalculated differently)
-- and simply reduces it to the single lowest-OTD% row, per the plan's
-- explicit validation method ("no separate recalculation").
--
-- Restricted to area_tier_valid_flag = true: "underperforms most" is a
-- tier-comparison framing (Urban/Metropolitan/Semi-Urban), so "Other" is
-- excluded here per DATA_CLEANING_PLAN.md Step 8 — consistent with how
-- Q02's worst-P90-area and every other area-tier ranking in this project
-- treats "Other".
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    a.area_name,
    COUNT(*) AS total_deliveries,
    ROUND(100.0 * COUNT(*) FILTER (WHERE NOT f.sla_breach_flag) / COUNT(*), 4) AS otd_rate_pct
FROM routeiq."FactDelivery" f
JOIN routeiq."DimArea" a ON a.area_key = f.area_key
WHERE a.area_tier_valid_flag = TRUE
GROUP BY a.area_name
ORDER BY otd_rate_pct ASC
LIMIT 1;
