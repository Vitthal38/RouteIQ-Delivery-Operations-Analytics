-- =============================================================================
-- Q07 — Weekend vs. weekday delivery time
-- Priority: P2 | SQL_ANALYSIS_PLAN.md
--
-- Feeds STATISTICAL_ANALYSIS.md Test 5 (Python Phase 2) as group-stats
-- prep, same scope boundary as Q03/Q13 — no t-test/p-value computed here.
-- is_weekend is read directly from FactDelivery (already engineered in
-- Phase 1, FEATURE_ENGINEERING.md #5) — not recalculated.
-- =============================================================================

SET search_path TO routeiq, public;

SELECT
    CASE WHEN f.is_weekend THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    COUNT(*) AS n,
    ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
    ROUND(
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY f.delivery_time_minutes)::numeric,
        2
    ) AS p90_delivery_time_minutes,
    ROUND(STDDEV(f.delivery_time_minutes)::numeric, 2) AS stddev_delivery_time_minutes
FROM routeiq."FactDelivery" f
GROUP BY f.is_weekend
ORDER BY day_type;

-- Reconciliation check: weekend + weekday counts must equal total clean row count
SELECT COUNT(*) AS total_deliveries FROM routeiq."FactDelivery";
