-- =============================================================================
-- Q09 — Are specific agents outlier-prone, or is delay evenly distributed?
-- Priority: P2 | SQL_ANALYSIS_PLAN.md
--
-- DIMAGENT LIMITATION (STAR_SCHEMA.md design decision, Phase 2/3 rule):
-- the source dataset has no true Agent_ID. DimAgent is an attribute-derived
-- dimension (distinct agent_age/agent_rating combinations), NOT individual
-- agents. This query therefore CANNOT identify whether specific individual
-- agents are outlier-prone — that would require a real Agent_ID that does
-- not exist in the source data. It is reframed, accurately, as: is delivery
-- time variance evenly distributed across agent-rating performance tiers,
-- or concentrated in specific tiers? This is attribute-based analysis, not
-- individual-agent tracking, and must never be narrated as the latter.
--
-- REMEDIATION (2026-08-16, per reports/sql_senior_audit.md HIGH finding):
-- The original implementation applied NTILE(4) directly to FactDelivery
-- rows (ORDER BY ag.agent_rating). With only ~26 distinct agent_rating
-- values across 43,594 rows, several values (4.5, 4.7, 4.9) have far more
-- tied rows than fit cleanly on one side of an equal-row-count bucket
-- boundary, so NTILE cut through those ties -- empirically confirmed:
-- rating 4.5 alone split 2,875/428 across tiers 1/2. Adding a tiebreaker
-- column would only make that split deterministic, not correct -- rows
-- sharing the identical rating value would still land in different tiers.
--
-- Fix: NTILE(4) is now applied to the small set of DISTINCT agent_rating
-- values (one row per unique rating -- no ties possible at that grain),
-- and every fact row inherits its rating's single assigned tier via a
-- join. This preserves the requested technique (NTILE "for performance
-- tiers", per SQL_ANALYSIS_PLAN.md's SQL Concepts column for Q09) and the
-- four-ordered-tiers business meaning, while guaranteeing that no two
-- rows sharing the same agent_rating can ever land in different tiers.
--
-- Documented trade-off (do not mistake this for the old equal-row-count
-- quartiles): because tiers are now assigned by rating VALUE, not by row
-- rank, tier row counts are uneven -- each tier holds whatever rows its
-- assigned rating values happen to carry. The output column is named
-- rating_tier, not rating_quartile, to avoid implying equal population.
-- =============================================================================

SET search_path TO routeiq, public;

WITH distinct_ratings AS (
    SELECT DISTINCT ag.agent_rating
    FROM routeiq."DimAgent" ag
    WHERE ag.agent_rating_valid_flag = TRUE
),
rating_tier_assignment AS (
    -- NTILE applied at the distinct-value grain: each unique rating value
    -- appears exactly once here, so there is no tie for NTILE to cut
    -- through -- every value gets one, and only one, tier.
    SELECT
        agent_rating,
        NTILE(4) OVER (ORDER BY agent_rating) AS rating_tier
    FROM distinct_ratings
),
rating_tiered AS (
    SELECT
        f.delivery_time_minutes,
        rta.rating_tier
    FROM routeiq."FactDelivery" f
    JOIN routeiq."DimAgent" ag ON ag.agent_key = f.agent_key
    JOIN rating_tier_assignment rta ON rta.agent_rating = ag.agent_rating
    WHERE ag.agent_rating_valid_flag = TRUE
)
SELECT
    rating_tier,
    COUNT(*) AS n,
    ROUND(AVG(delivery_time_minutes)::numeric, 2) AS avg_delivery_time_minutes,
    ROUND(STDDEV(delivery_time_minutes)::numeric, 2) AS stddev_delivery_time_minutes,
    ROUND(
        (STDDEV(delivery_time_minutes) / NULLIF(AVG(delivery_time_minutes), 0))::numeric,
        4
    ) AS coefficient_of_variation
FROM rating_tiered
GROUP BY rating_tier
ORDER BY rating_tier;
