-- =============================================================================
-- Q26 - Is the agent-age relationship gradual, or a step? (attribute-level only)
-- Business question: at what age, if any, does breach rate suddenly change?
-- Same LAG()-based adjacent-jump method as Q25. On this data the step is at age 30; a change at
-- one exact round number is unusual for a real workforce (see docs/limitations.md, "Data realism").
-- =============================================================================
SET search_path TO routeiq, public;

WITH by_age AS (
    SELECT agent_age,
           COUNT(*)         AS n,
           SUM(breach_flag) AS breaches
    FROM routeiq.vw_analytical_deliveries
    GROUP BY agent_age
    HAVING COUNT(*) >= 100
),
with_rate AS (
    SELECT agent_age, n, breaches, breaches::float8 / n AS breach_rate
    FROM by_age
),
with_jump AS (
    SELECT agent_age,
           n,
           ROUND((100 * breach_rate)::numeric, 4)                                   AS breach_rate_pct,
           LAG(agent_age)      OVER (ORDER BY agent_age)                            AS prev_age,
           LAG(n)              OVER (ORDER BY agent_age)                            AS prev_n,
           ROUND((100 * LAG(breach_rate) OVER (ORDER BY agent_age))::numeric, 4)    AS prev_breach_rate_pct,
           ROUND((100 * (breach_rate - LAG(breach_rate) OVER (ORDER BY agent_age)))::numeric, 4) AS jump_pts
    FROM with_rate
)
SELECT agent_age, n, prev_age, prev_n, prev_breach_rate_pct, breach_rate_pct, jump_pts,
       RANK() OVER (ORDER BY ABS(jump_pts) DESC NULLS LAST) AS step_rank
FROM with_jump
ORDER BY agent_age;
