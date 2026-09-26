-- =============================================================================
-- Q26 - Is the agent-age relationship gradual or a step? (attribute-level only)
-- Business question: does breach risk change gradually with age, or at one age?
-- Same method as Q25 (candidate cuts ranked by step-model log-likelihood).
-- On this data the best cut is age 30; a step at a round number is unusual for real
-- workforce data (see docs/limitations.md, "Data realism").
-- =============================================================================
SET search_path TO routeiq, public;

WITH cuts AS (
    SELECT generate_series(21, 39) AS cut
),
agg AS (
    SELECT c.cut,
           COUNT(*) FILTER (WHERE v.agent_age <  c.cut)                 AS n_below,
           SUM(v.breach_flag) FILTER (WHERE v.agent_age <  c.cut)       AS k_below,
           COUNT(*) FILTER (WHERE v.agent_age >= c.cut)                 AS n_above,
           SUM(v.breach_flag) FILTER (WHERE v.agent_age >= c.cut)       AS k_above
    FROM cuts c CROSS JOIN routeiq.vw_analytical_deliveries v
    GROUP BY c.cut
),
scored AS (
    SELECT *,
           k_below::float8 / n_below AS rate_below,
           k_above::float8 / n_above AS rate_above,
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
