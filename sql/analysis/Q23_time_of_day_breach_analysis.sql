-- =============================================================================
-- Q23 - When do SLA breaches happen? (time of day)
-- Business question: which hours carry the breaches, and is volume or risk the reason?
-- Output: per order hour - volume, breaches, breach rate, share of deliveries, share of
-- breaches and LIFT (share of breaches / share of deliveries; 1.0 = proportional).
-- Read with Q28/docs: traffic level is almost a function of order hour in this data.
-- Uses: window functions over aggregates, view vw_analytical_deliveries.
-- =============================================================================
SET search_path TO routeiq, public;

SELECT
    order_hour,
    hour_band,
    COUNT(*)                                                       AS n,
    SUM(breach_flag)                                               AS breaches,
    ROUND(100.0 * AVG(breach_flag), 4)                             AS breach_rate_pct,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4)             AS share_of_deliveries_pct,
    ROUND(100.0 * SUM(breach_flag) / SUM(SUM(breach_flag)) OVER (), 4) AS share_of_breaches_pct,
    ROUND((SUM(breach_flag)::numeric / SUM(SUM(breach_flag)) OVER ())
          / (COUNT(*)::numeric / SUM(COUNT(*)) OVER ()), 4)        AS lift
FROM routeiq.vw_analytical_deliveries
GROUP BY order_hour, hour_band
ORDER BY order_hour;
