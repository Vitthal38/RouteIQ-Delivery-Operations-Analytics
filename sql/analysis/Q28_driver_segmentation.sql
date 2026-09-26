-- =============================================================================
-- Q28 - Which segments concentrate the breaches?
-- Business question: combine the three biggest associated factors (rating group x age group x
-- traffic) and rank the cells by breach volume. Where would an operations team look first?
-- Output: every cell with n, breaches, breach rate, share of all breaches, cumulative share
-- (deterministic order: breaches DESC, then cell name) and a small-sample flag (n < 200).
-- Attribute-level only; association, not causation.
-- =============================================================================
SET search_path TO routeiq, public;

WITH cells AS (
    SELECT
        CASE WHEN rating_lt_4_5 = 1 THEN 'rating < 4.5' ELSE 'rating >= 4.5' END AS rating_group,
        CASE WHEN age_ge_30 = 1 THEN 'age >= 30' ELSE 'age < 30' END           AS age_group,
        traffic,
        COUNT(*)         AS n,
        SUM(breach_flag) AS breaches
    FROM routeiq.vw_analytical_deliveries
    WHERE rating_lt_4_5 IS NOT NULL
    GROUP BY 1, 2, 3
)
SELECT
    rating_group || ' | ' || age_group || ' | ' || traffic                              AS segment,
    rating_group, age_group, traffic, n, breaches,
    ROUND(100.0 * breaches / n, 4)                                                       AS breach_rate_pct,
    ROUND(100.0 * breaches / SUM(breaches) OVER (), 4)                                   AS share_of_breaches_pct,
    ROUND(100.0 * SUM(breaches) OVER (ORDER BY breaches DESC, rating_group, age_group, traffic)
          / SUM(breaches) OVER (), 4)                                                    AS cumulative_share_pct,
    (n < 200)                                                                            AS small_sample_flag
FROM cells
ORDER BY breaches DESC, rating_group, age_group, traffic;
