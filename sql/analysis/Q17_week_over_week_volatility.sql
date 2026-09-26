-- =============================================================================
-- Q17 — Week-over-week volatility in delivery time
-- Priority: P2 | SQL_ANALYSIS_PLAN.md
--
-- KPI: Week-over-Week Delivery Time Volatility (KPI_DEFINITIONS.md #8).
-- LAG() output is re-derivable by manual subtraction of two adjacent
-- weekly values, per the plan's validation method — verified in
-- reports/sql_analysis_validation.md.
--
-- Limitation restated (KPI_DEFINITIONS.md #8): only 8 distinct weeks are
-- observed, two of them partial (see Q11) — week-over-week % change is
-- reported for every truly adjacent pair, but the short window limits how
-- much can be said about genuine trend versus noise.
--
-- REMEDIATION (2026-08-16, per reports/sql_senior_audit.md MEDIUM finding):
-- Week 8 has zero rows (no orders 2022-02-19 to 2022-02-28) — the
-- observed week sequence is 6, 7, 9, 10, 11, 12, 13, 14, not 6-14
-- consecutively. Neither FEATURE_ENGINEERING.md #7, KPI_DEFINITIONS.md
-- #8, DATASET_OVERVIEW.md, nor ASSUMPTIONS.md states whether this gap
-- represents zero business activity or an unavailable reporting period —
-- that ambiguity is intentionally NOT resolved here, and does not need to
-- be: AVG()/PERCENTILE_CONT() require at least one delivery row, so no
-- delivery-time metric is computable for week 8 under either
-- interpretation. What the previous version got wrong was not "what is
-- week 8's value" but that LAG() OVER (ORDER BY week_number) silently
-- treated week 9's prior ROW (week 7) as its prior WEEK, understating the
-- true 2-week gap between them.
--
-- Fix: LAG() is retained (not replaced). weeks_since_prior_observed_week
-- makes the true calendar gap explicit for every row. Every "vs. prior
-- week" delta is computed only when that gap is exactly 1 -- otherwise it
-- is NULL, and is_consecutive_week_comparison is FALSE -- so a
-- non-adjacent comparison is never silently presented as a normal
-- week-over-week change.
-- =============================================================================

SET search_path TO routeiq, public;

WITH weekly AS (
    SELECT
        d.week_number,
        COUNT(*) AS n,
        ROUND(AVG(f.delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
        ROUND(
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY f.delivery_time_minutes)::numeric,
            2
        ) AS p90_delivery_time_minutes
    FROM routeiq."FactDelivery" f
    JOIN routeiq."DimDate" d ON d.date_key = f.date_key
    GROUP BY d.week_number
),
weekly_with_gap AS (
    SELECT
        week_number,
        n,
        avg_delivery_time_minutes,
        p90_delivery_time_minutes,
        LAG(week_number) OVER (ORDER BY week_number) AS prior_observed_week_number,
        week_number - LAG(week_number) OVER (ORDER BY week_number) AS weeks_since_prior_observed_week,
        LAG(avg_delivery_time_minutes) OVER (ORDER BY week_number) AS prior_week_avg_raw,
        LAG(p90_delivery_time_minutes) OVER (ORDER BY week_number) AS prior_week_p90_raw
    FROM weekly
)
SELECT
    week_number,
    n,
    avg_delivery_time_minutes,
    prior_observed_week_number,
    weeks_since_prior_observed_week,
    (weeks_since_prior_observed_week = 1) AS is_consecutive_week_comparison,
    CASE WHEN weeks_since_prior_observed_week = 1 THEN prior_week_avg_raw END AS prior_week_avg,
    CASE WHEN weeks_since_prior_observed_week = 1 THEN
        ROUND(100.0 * (avg_delivery_time_minutes - prior_week_avg_raw) / NULLIF(prior_week_avg_raw, 0), 2)
    END AS avg_pct_change_vs_prior_week,
    p90_delivery_time_minutes,
    CASE WHEN weeks_since_prior_observed_week = 1 THEN prior_week_p90_raw END AS prior_week_p90,
    CASE WHEN weeks_since_prior_observed_week = 1 THEN
        ROUND(100.0 * (p90_delivery_time_minutes - prior_week_p90_raw) / NULLIF(prior_week_p90_raw, 0), 2)
    END AS p90_pct_change_vs_prior_week
FROM weekly_with_gap
ORDER BY week_number;
