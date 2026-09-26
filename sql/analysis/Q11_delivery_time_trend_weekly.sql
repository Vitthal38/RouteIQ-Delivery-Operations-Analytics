-- =============================================================================
-- Q11 — Trend in delivery time over the observed period
-- Priority: P0 | SQL_ANALYSIS_PLAN.md
--
-- KPI: Delivery Time Trend (Weekly) (KPI_DEFINITIONS.md #3/#4 trend view;
-- matches DAX_MEASURE_PLAN.md's "Delivery Time Trend (Weekly)" measure).
--
-- Partial-week handling: distinct_days_observed is computed from DimDate
-- (not assumed) so a reader can see exactly which weeks have fewer than 7
-- calendar days of data, per FEATURE_ENGINEERING.md #7's edge case — no
-- week is silently treated as a full week. The observed date range has a
-- known gap (2022-02-19 to 2022-02-28 has no orders at all), which this
-- query surfaces as a low distinct_days_observed count rather than hiding it.
-- =============================================================================

SET search_path TO routeiq, public;

WITH weekly AS (
    SELECT
        d.week_number,
        MIN(d.full_date) AS week_first_observed_date,
        MAX(d.full_date) AS week_last_observed_date,
        COUNT(DISTINCT d.full_date) AS distinct_days_observed,
        COUNT(*) AS n,
        ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
        ROUND(
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY f.delivery_time_minutes)::numeric,
            2
        ) AS p90_delivery_time_minutes
    FROM routeiq."FactDelivery" f
    JOIN routeiq."DimDate" d ON d.date_key = f.date_key
    GROUP BY d.week_number
)
SELECT
    week_number,
    week_first_observed_date,
    week_last_observed_date,
    distinct_days_observed,
    (distinct_days_observed < 7) AS partial_week_flag,
    n,
    avg_delivery_time_minutes,
    p90_delivery_time_minutes,
    ROUND(
        (avg_delivery_time_minutes - LAG(avg_delivery_time_minutes) OVER (ORDER BY week_number)),
        2
    ) AS avg_delta_vs_prior_week
FROM weekly
ORDER BY week_number;
