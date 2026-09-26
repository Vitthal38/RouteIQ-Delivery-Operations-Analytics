-- =============================================================================
-- Q24 - Is preparation time associated with breach or delivery time?
-- Business question: is prep time an operational lever worth acting on?
-- Output (GROUPING SETS -> one result): prep alone, prep x traffic, prep x area.
-- Finding on this data: no association (see docs/analytical_findings.md); the query is kept
-- because "no effect" is a decision-relevant answer.
-- =============================================================================
SET search_path TO routeiq, public;

SELECT
    CASE
        WHEN traffic IS NOT NULL THEN 'prep x traffic'
        WHEN area    IS NOT NULL THEN 'prep x area'
        ELSE 'prep'
    END                                          AS cut,
    prep_time_minutes,
    traffic,
    area,
    COUNT(*)                                     AS n,
    SUM(breach_flag)                             AS breaches,
    ROUND(100.0 * AVG(breach_flag), 4)           AS breach_rate_pct,
    ROUND(AVG(delivery_time_minutes), 2)         AS avg_delivery_minutes
FROM routeiq.vw_analytical_deliveries
GROUP BY GROUPING SETS ((prep_time_minutes),
                        (prep_time_minutes, traffic),
                        (prep_time_minutes, area))
ORDER BY cut, prep_time_minutes, traffic NULLS FIRST, area NULLS FIRST;
