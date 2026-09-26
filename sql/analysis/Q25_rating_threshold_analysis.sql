-- =============================================================================
-- Q25 - Is the agent-rating relationship a slope or a step? (attribute-level only)
-- Business question: below which rating do breaches jump? (No agent identifier exists;
-- rating is an attribute of the delivery record, never an individual agent.)
-- Method: for every candidate cut c, compare breach rate below (< c) and at/above (>= c);
-- rank cuts by the log-likelihood of the two-group step model. The best cut is the step.
-- Caution: rating may be an OUTCOME of delivery performance (reverse causation).
-- =============================================================================
SET search_path TO routeiq, public;

WITH cuts AS (
    SELECT generate_series(30, 50)::numeric / 10 AS cut            -- 3.0 ... 5.0
),
r AS (
    SELECT agent_rating, breach_flag
    FROM routeiq.vw_analytical_deliveries
    WHERE agent_rating IS NOT NULL
),
agg AS (
    SELECT c.cut,
           COUNT(*) FILTER (WHERE r.agent_rating <  c.cut)                    AS n_below,
           SUM(r.breach_flag) FILTER (WHERE r.agent_rating <  c.cut)          AS k_below,
           COUNT(*) FILTER (WHERE r.agent_rating >= c.cut)                    AS n_above,
           SUM(r.breach_flag) FILTER (WHERE r.agent_rating >= c.cut)          AS k_above
    FROM cuts c CROSS JOIN r
    GROUP BY c.cut
),
scored AS (
    SELECT *,
           k_below::float8 / n_below AS rate_below,
           k_above::float8 / n_above AS rate_above,
           -- log-likelihood of the two-group step model (0 * ln 0 := 0)
           CASE WHEN k_below IN (0, n_below) THEN 0
                ELSE k_below * LN(k_below::float8 / n_below) + (n_below - k_below) * LN(1 - k_below::float8 / n_below) END
         + CASE WHEN k_above IN (0, n_above) THEN 0
                ELSE k_above * LN(k_above::float8 / n_above) + (n_above - k_above) * LN(1 - k_above::float8 / n_above) END
           AS loglik_step_model
    FROM agg
    WHERE n_below >= 100 AND n_above >= 100
)
SELECT cut,
       n_below,
       n_above                                             AS n_at_or_above,
       ROUND((100 * rate_below)::numeric, 4)               AS breach_rate_below_pct,
       ROUND((100 * rate_above)::numeric, 4)               AS breach_rate_at_or_above_pct,
       ROUND((100 * (rate_below - rate_above))::numeric, 4) AS risk_diff_pts,
       ROUND((rate_below / NULLIF(rate_above, 0))::numeric, 4) AS risk_ratio,
       ROUND(loglik_step_model::numeric, 2)                AS loglik_step_model,
       RANK() OVER (ORDER BY loglik_step_model DESC)       AS step_rank
FROM scored
ORDER BY cut;
