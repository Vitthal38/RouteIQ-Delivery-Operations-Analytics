-- =============================================================================
-- Q18 — Are longer delivery times concentrated in specific categories?
-- Priority: P2 | SQL_ANALYSIS_PLAN.md
--
-- Same underlying cut as Q06 (category x delivery time), reframed around
-- concentration/variance rather than a simple average ranking, per the
-- plan's own note ("Same as Q6, framed as concentration/variance" —
-- "Same as Q6" also for validation method). Kept as a separate file per
-- the one-file-per-question rule; the added STDDEV/coefficient-of-variation
-- columns are what this question's framing specifically asks for.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    c.category_name,
    COUNT(*) AS n,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
    ROUND(STDDEV(f.delivery_time_minutes)::numeric, 2) AS stddev_delivery_time_minutes,
    ROUND(
        (STDDEV(f.delivery_time_minutes) / NULLIF(AVG(f.delivery_time_minutes), 0))::numeric,
        4
    ) AS coefficient_of_variation
FROM routeiq."FactDelivery" f
JOIN routeiq."DimCategory" c ON c.category_key = f.category_key
GROUP BY c.category_name
ORDER BY stddev_delivery_time_minutes DESC;
