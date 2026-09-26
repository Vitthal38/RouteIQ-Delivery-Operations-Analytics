-- =============================================================================
-- Q15 — Agent age vs. delivery time or rating
-- Priority: P2 | SQL_ANALYSIS_PLAN.md
--
-- Both correlations computed only on rows passing BOTH validity flags
-- (agent_age_valid_flag AND agent_rating_valid_flag), exactly as
-- SQL_ANALYSIS_PLAN.md's validation method specifies. Row counts reported
-- explicitly. CORR() is descriptive only — no hypothesis test performed.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    COUNT(*) AS n_valid_age_and_rating_rows,
    ROUND(CORR(ag.agent_age, f.delivery_time_minutes)::numeric, 4) AS age_vs_delivery_time_r,
    ROUND(CORR(ag.agent_age, ag.agent_rating)::numeric, 4) AS age_vs_rating_r
FROM routeiq."FactDelivery" f
JOIN routeiq."DimAgent" ag ON ag.agent_key = f.agent_key
WHERE ag.agent_age_valid_flag = TRUE
  AND ag.agent_rating_valid_flag = TRUE;
