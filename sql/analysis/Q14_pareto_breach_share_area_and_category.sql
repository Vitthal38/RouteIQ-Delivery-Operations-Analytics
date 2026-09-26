-- =============================================================================
-- Q14 — % of deliveries from top 20% highest-delay areas/categories (Pareto)
-- Priority: P1 | SQL_ANALYSIS_PLAN.md
--
-- KPI: Delay Root-Cause Share / Pareto Concentration (KPI_DEFINITIONS.md #7).
--
-- INTERPRETATION NOTE (disclosed per this project's convention for
-- ambiguous plan wording, same treatment as Q19's "adverse weather"):
-- SQL_ANALYSIS_PLAN.md's question text ("areas/categories") does not
-- specify whether this is one pooled ranking across both dimensions or
-- two separate single-dimension cuts. Pooling area and category segments
-- into a single ranked list would compare apples to oranges (they are not
-- the same kind of segment, and Q20 already owns the combined area x
-- traffic 2-D cut). This file therefore implements TWO independent Pareto
-- rankings — by area, then by category — each reaching its own cumulative
-- percentage, ranked by breach count descending, using the frozen
-- sla_breach_flag.
--
-- "Top 20% of segments" is computed exactly (CEIL(0.2 * segment_count)),
-- not eyeballed, per the plan's own validation method.
--
-- REMEDIATION (2026-08-16, per reports/sql_senior_audit.md MEDIUM finding):
-- Category cut has a confirmed tie (Snacks and Electronics both at 689
-- breaches). RANK() correctly gave both rows rank 2 -- that logic is
-- unchanged. The running-total SUM() OVER window, however, had no
-- secondary ORDER BY key, so PostgreSQL was not guaranteed to process the
-- two tied rows in a stable order -- the exact intermediate
-- cumulative_breach_share_pct shown for Snacks vs. Electronics individually
-- was not reproducible across re-runs (the grand total after both rows
-- was always correct regardless). Fixed by adding the segment's own name
-- as a documented, stable secondary sort key to the running-total window
-- ONLY -- the RANK() window is untouched, so tie behavior (both rows
-- sharing rank 2) is unchanged, breach counts are unchanged, and the
-- Pareto/top-20% classification is unchanged.
-- =============================================================================

SET search_path TO routeiq, public;

-- ---- Pareto cut 1: by Area ----
WITH area_breaches AS (
    SELECT
        a.area_name,
        COUNT(*) FILTER (WHERE f.sla_breach_flag) AS breach_count
    FROM routeiq."FactDelivery" f
    JOIN routeiq."DimArea" a ON a.area_key = f.area_key
    GROUP BY a.area_name
),
area_ranked AS (
    SELECT
        area_name,
        breach_count,
        RANK() OVER (ORDER BY breach_count DESC) AS breach_rank,
        -- Secondary key (area_name) makes row-processing order deterministic
        -- for any tied breach_count; RANK() above is intentionally NOT given
        -- this secondary key, so tie behavior there is unchanged.
        SUM(breach_count) OVER (ORDER BY breach_count DESC, area_name ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_breach_total,
        SUM(breach_count) OVER () AS total_breaches,
        COUNT(*) OVER () AS segment_count
    FROM area_breaches
)
SELECT
    area_name,
    breach_count,
    breach_rank,
    segment_count,
    CEIL(0.2 * segment_count) AS top_20_pct_segment_cutoff,
    (breach_rank <= CEIL(0.2 * segment_count)) AS in_top_20_pct_segments,
    ROUND(100.0 * running_breach_total / NULLIF(total_breaches, 0), 4) AS cumulative_breach_share_pct
FROM area_ranked
ORDER BY breach_rank;

-- ---- Pareto cut 2: by Category ----
WITH category_breaches AS (
    SELECT
        c.category_name,
        COUNT(*) FILTER (WHERE f.sla_breach_flag) AS breach_count
    FROM routeiq."FactDelivery" f
    JOIN routeiq."DimCategory" c ON c.category_key = f.category_key
    GROUP BY c.category_name
),
category_ranked AS (
    SELECT
        category_name,
        breach_count,
        RANK() OVER (ORDER BY breach_count DESC) AS breach_rank,
        -- Secondary key (category_name) makes row-processing order
        -- deterministic for the confirmed tie (Snacks / Electronics, both
        -- 689 breaches); RANK() above intentionally does NOT get this
        -- secondary key, so both rows continue to share rank 2 as before.
        SUM(breach_count) OVER (ORDER BY breach_count DESC, category_name ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_breach_total,
        SUM(breach_count) OVER () AS total_breaches,
        COUNT(*) OVER () AS segment_count
    FROM category_breaches
)
SELECT
    category_name,
    breach_count,
    breach_rank,
    segment_count,
    CEIL(0.2 * segment_count) AS top_20_pct_segment_cutoff,
    (breach_rank <= CEIL(0.2 * segment_count)) AS in_top_20_pct_segments,
    ROUND(100.0 * running_breach_total / NULLIF(total_breaches, 0), 4) AS cumulative_breach_share_pct
FROM category_ranked
ORDER BY breach_rank;
