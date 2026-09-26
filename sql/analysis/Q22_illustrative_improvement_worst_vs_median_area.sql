-- =============================================================================
-- Q22 — Estimated improvement if worst area matched median area's delivery time
-- Priority: P1 | SQL_ANALYSIS_PLAN.md
--
-- ILLUSTRATIVE ESTIMATE ONLY — NOT A GUARANTEED SAVINGS FIGURE.
-- Per ASSUMPTIONS.md A8, no cost/financial field exists in the source
-- dataset; this is a delivery-TIME delta, not a dollar/rupee figure, and
-- must never be presented as a measured or committed operational result.
--
-- RANKING DEFINITION (disclosed, since the plan does not fully specify
-- it): "worst" and "median" area are defined by the OTD% ranking already
-- established in Q08/Q16 (lowest OTD% = worst), restricted to
-- area_tier_valid_flag = true areas, for consistency with how "worst
-- area" is defined everywhere else in this project. The delta itself is
-- then computed on AVERAGE delivery time for those two areas, per the
-- plan's own formula: (worst-area avg - median-area avg) x worst-area volume.
-- =============================================================================

SET search_path TO routeiq, public;

WITH area_stats AS (
    SELECT
        a.area_name,
        COUNT(*) AS n,
        ROUND(100.0 * COUNT(*) FILTER (WHERE NOT f.sla_breach_flag) / COUNT(*), 4) AS otd_rate_pct,
        ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes
    FROM routeiq."FactDelivery" f
    JOIN routeiq."DimArea" a ON a.area_key = f.area_key
    WHERE a.area_tier_valid_flag = TRUE
    GROUP BY a.area_name
),
ranked AS (
    SELECT
        area_name,
        n,
        otd_rate_pct,
        avg_delivery_time_minutes,
        ROW_NUMBER() OVER (ORDER BY otd_rate_pct ASC) AS otd_rank_worst_first,
        COUNT(*) OVER () AS area_count
    FROM area_stats
),
worst AS (
    SELECT area_name, n, avg_delivery_time_minutes
    FROM ranked WHERE otd_rank_worst_first = 1
),
median_area AS (
    SELECT area_name, avg_delivery_time_minutes
    FROM ranked WHERE otd_rank_worst_first = CEIL(area_count::numeric / 2)
)
SELECT
    worst.area_name AS worst_area,
    worst.n AS worst_area_deliveries,
    worst.avg_delivery_time_minutes AS worst_area_avg_minutes,
    median_area.area_name AS median_area,
    median_area.avg_delivery_time_minutes AS median_area_avg_minutes,
    ROUND(worst.avg_delivery_time_minutes - median_area.avg_delivery_time_minutes, 2) AS avg_minutes_delta,
    ROUND(
        (worst.avg_delivery_time_minutes - median_area.avg_delivery_time_minutes) * worst.n,
        2
    ) AS illustrative_total_minutes_saved_if_matched,
    'Illustrative estimate only -- not a measured or guaranteed savings figure (ASSUMPTIONS.md A8)' AS caveat
FROM worst, median_area;
