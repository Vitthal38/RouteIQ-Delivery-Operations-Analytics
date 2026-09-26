-- =============================================================================
-- 07_load_fact.sql — RouteIQ Phase 2
-- Loads FactDelivery from the staged cleaned dataset, resolving each
-- dimension's surrogate key by joining on its natural attribute(s).
--
-- SLA handling (per this phase's explicit rule): sla_threshold_minutes is
-- sourced by joining routeiq.stg_sla_reference on Category — i.e. from the
-- frozen data/cleaned/sla_reference.csv loaded in 06 — NOT from
-- stg_cleaned_delivery's own already-frozen sla_threshold_minutes column.
-- This makes FactDelivery's value independently traceable to the frozen
-- reference through a real join, rather than an inherited column copy, and
-- is what 08_validation.sql cross-checks. No percentile is recalculated
-- anywhere in this script.
--
-- sla_breach_flag is computed here as a simple comparison against the
-- now-resolved frozen threshold (delivery_time_minutes > threshold) — this
-- is not a recalculation of the SLA rule itself, only its mechanical
-- application, exactly as FEATURE_ENGINEERING.md #3 and SLA_METHODOLOGY.md
-- specify.
--
-- agent_key resolution uses IS NOT DISTINCT FROM for agent_rating so that
-- the 54 rows with a NULL Agent_Rating correctly match the single DimAgent
-- row representing (that age, NULL rating), instead of matching nothing
-- (standard SQL '=' never matches NULL to NULL).
--
-- Run as: psql -U postgres -f 07_load_fact.sql
-- (Run only after 06_load_dimensions.sql has populated every dimension.)
-- =============================================================================

SET search_path TO routeiq, public;

INSERT INTO routeiq."FactDelivery" (
    order_id,
    agent_key,
    date_key,
    area_key,
    category_key,
    weather_traffic_key,
    vehicle_key,
    order_time,
    pickup_time,
    delivery_time_minutes,
    prep_time_minutes,
    distance_km,
    sla_threshold_minutes,
    sla_breach_flag,
    is_weekend,
    week_number,
    agent_rating_available_flag,
    coordinates_valid_flag
)
SELECT
    s."Order_ID",
    da.agent_key,
    dd.date_key,
    dar.area_key,
    dc.category_key,
    dwt.weather_traffic_key,
    dv.vehicle_key,
    s."Order_Time",
    s."Pickup_Time",
    s."Delivery_Time",
    s.prep_time_minutes,
    s.distance_km,
    sref.sla_threshold_minutes,                              -- from frozen reference, not stg_cleaned_delivery
    (s."Delivery_Time" > sref.sla_threshold_minutes),         -- computed against the frozen threshold
    s.is_weekend,
    s.week_number,
    s.agent_rating_available_flag,
    s.coordinates_valid_flag
FROM routeiq.stg_cleaned_delivery s
JOIN routeiq."DimAgent" da
    ON da.agent_age = s."Agent_Age"
   AND da.agent_rating IS NOT DISTINCT FROM s."Agent_Rating"
JOIN routeiq."DimDate" dd
    ON dd.full_date = s."Order_Date"
JOIN routeiq."DimArea" dar
    ON dar.area_name = s."Area"
JOIN routeiq."DimCategory" dc
    ON dc.category_name = s."Category"
JOIN routeiq."DimWeatherTraffic" dwt
    ON dwt.weather = s."Weather"
   AND dwt.traffic = s."Traffic"
JOIN routeiq."DimVehicle" dv
    ON dv.vehicle_name = s."Vehicle"
JOIN routeiq.stg_sla_reference sref
    ON sref."Category" = s."Category";
