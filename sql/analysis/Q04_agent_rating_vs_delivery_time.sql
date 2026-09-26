-- =============================================================================
-- Q04 — Relationship between agent rating and delivery time
-- Priority: P1 | SQL_ANALYSIS_PLAN.md
--
-- KPI: Agent Rating-Delivery Time Relationship (KPI_DEFINITIONS.md #6).
-- Filtered to agent_rating_valid_flag = true only — this excludes both the
-- true-null ratings and the (pre-Step-3-exclusion) out-of-range 6.0 rows,
-- per DAX_MEASURE_PLAN.md's explicit warning not to filter loosely by
-- "IS NOT NULL" alone. Row count used is reported explicitly.
--
-- CORR() below computes the Pearson correlation coefficient as a plain SQL
-- aggregate (descriptive statistic) — this is not a hypothesis test; no
-- p-value or significance claim is produced. The formal test lives in
-- STATISTICAL_ANALYSIS.md Test 3 (Python Phase 2), out of scope here.
-- =============================================================================

SET search_path TO routeiq, public;

-- Correlation coefficient + row count used
SELECT
    COUNT(*) AS n_valid_rating_rows,
    ROUND(CORR(ag.agent_rating, f.delivery_time_minutes)::numeric, 4) AS pearson_r
FROM routeiq."FactDelivery" f
JOIN routeiq."DimAgent" ag ON ag.agent_key = f.agent_key
WHERE ag.agent_rating_valid_flag = TRUE;

-- Supporting view: average delivery time by rating band (0.5-point increments)
SELECT
    FLOOR(ag.agent_rating / 0.5) * 0.5 AS rating_band_floor,
    COUNT(*) AS n,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes
FROM routeiq."FactDelivery" f
JOIN routeiq."DimAgent" ag ON ag.agent_key = f.agent_key
WHERE ag.agent_rating_valid_flag = TRUE
GROUP BY rating_band_floor
ORDER BY rating_band_floor;
