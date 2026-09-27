-- =============================================================================
-- Q27 - How sensitive are the breach numbers to the SLA definition?
-- Business question: the SLA is an analyst-defined benchmark (category-level P75, in-sample),
-- so ~25% breach is expected by construction. What happens at P70 / P75 / P80 / P90?
-- Thresholds are recomputed per category with PERCENTILE_CONT (linear interpolation = numpy
-- default = DAX PERCENTILE.INC). At P75 this reproduces the frozen flag exactly (Q29 checks it).
-- Output: overall, by traffic, by area, by rating group - for each percentile.
-- =============================================================================
SET search_path TO routeiq, public;

WITH pcts AS (
    SELECT unnest(ARRAY[0.70, 0.75, 0.80, 0.90]::float8[]) AS pct
),
thr AS (
    SELECT p.pct, v.category,
           PERCENTILE_CONT(p.pct) WITHIN GROUP (ORDER BY v.delivery_time_minutes) AS threshold_minutes
    FROM routeiq.vw_analytical_deliveries v CROSS JOIN pcts p
    GROUP BY p.pct, v.category
),
flagged AS (
    SELECT t.pct, v.traffic, v.area,
           CASE WHEN v.rating_lt_4_5 IS NULL THEN 'no rating'
                WHEN v.rating_lt_4_5 = 1 THEN 'rating < 4.5' ELSE 'rating >= 4.5' END AS rating_group,
           (v.delivery_time_minutes > t.threshold_minutes)::int AS breach_at_pct
    FROM routeiq.vw_analytical_deliveries v
    JOIN thr t ON t.category = v.category
)
SELECT pct AS percentile,
       CASE WHEN traffic IS NOT NULL THEN 'traffic'
            WHEN area IS NOT NULL THEN 'area'
            WHEN rating_group IS NOT NULL THEN 'rating_group'
            ELSE 'overall' END                           AS cut,
       COALESCE(traffic, area, rating_group, 'all')      AS level,
       COUNT(*)                                          AS n,
       SUM(breach_at_pct)                                AS breaches,
       ROUND(100.0 * AVG(breach_at_pct), 4)              AS breach_rate_pct
FROM flagged
GROUP BY GROUPING SETS ((pct), (pct, traffic), (pct, area), (pct, rating_group))
ORDER BY pct, cut, level;
