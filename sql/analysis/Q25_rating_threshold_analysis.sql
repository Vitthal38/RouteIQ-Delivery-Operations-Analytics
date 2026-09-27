-- =============================================================================
-- Q25 - Is the agent-rating relationship a gradual slope, or a step? (attribute-level only)
-- Business question: at what rating, if any, does breach rate suddenly change? (No agent
-- identifier exists; rating is an attribute of the delivery record, never an individual agent.)
-- Method: breach rate by exact rating (dropping ratings with fewer than 100 deliveries, whose
-- jumps would be noise), then LAG() to get the jump to each value from the one before it.
-- The single largest jump marks the step - this is a descriptive comparison, not a fitted model.
-- Caution: rating may be an OUTCOME of delivery performance (reverse causation).
-- =============================================================================
SET search_path TO routeiq, public;

WITH by_rating AS (
    SELECT agent_rating,
           COUNT(*)         AS n,
           SUM(breach_flag) AS breaches
    FROM routeiq.vw_analytical_deliveries
    WHERE agent_rating IS NOT NULL
    GROUP BY agent_rating
    HAVING COUNT(*) >= 100                      -- drop ratings too rare to trust a jump from
),
with_rate AS (
    SELECT agent_rating, n, breaches, breaches::float8 / n AS breach_rate
    FROM by_rating
),
with_jump AS (
    SELECT agent_rating,
           n,
           ROUND((100 * breach_rate)::numeric, 4)                                   AS breach_rate_pct,
           LAG(agent_rating)   OVER (ORDER BY agent_rating)                         AS prev_rating,
           LAG(n)              OVER (ORDER BY agent_rating)                         AS prev_n,
           ROUND((100 * LAG(breach_rate) OVER (ORDER BY agent_rating))::numeric, 4) AS prev_breach_rate_pct,
           ROUND((100 * (breach_rate - LAG(breach_rate) OVER (ORDER BY agent_rating)))::numeric, 4) AS jump_pts
    FROM with_rate
)
SELECT agent_rating, n, prev_rating, prev_n, prev_breach_rate_pct, breach_rate_pct, jump_pts,
       RANK() OVER (ORDER BY ABS(jump_pts) DESC NULLS LAST) AS step_rank
FROM with_jump
ORDER BY agent_rating;
