-- =============================================================================
-- 09_create_analytical_view.sql
-- The controlled analytical dataset as a view: one row per delivery, every derived
-- feature defined ONCE. SQL analysis (Q23-Q30) and the Python analytical dataset
-- (data/processed/analytical_deliveries.csv) use the same definitions, and
-- tests/test_reconciliation.py checks that the two agree.
--
-- Definitions (see docs/data_dictionary.md):
--   breach_flag      : delivery_time_minutes > sla_threshold_minutes (strict >).
--                      Recomputed here from the frozen threshold, not read from the flag.
--   is_peak_hour     : order hour 17-23. This is the rule "hourly volume >= 2x the median
--                      hourly volume", which selects 17:00-23:59 on this data (Python asserts it).
--   hour_band        : exploratory bands chosen AFTER inspecting the hourly profile.
--   rating_lt_4_5    : 1 if agent_rating < 4.5; NULL when the rating is missing/invalid.
--   age_ge_30        : 1 if agent_age >= 30.
--   agent_rating     : NULL for rows with no valid rating (54 rows).
--
-- Run as: psql -U postgres -f 09_create_analytical_view.sql
-- =============================================================================

SET search_path TO routeiq, public;

CREATE OR REPLACE VIEW routeiq.vw_analytical_deliveries AS
SELECT
    f.delivery_key,
    f.order_id,
    d.full_date                                              AS order_date,
    f.week_number,
    f.is_weekend::int                                        AS is_weekend,
    EXTRACT(HOUR FROM f.order_time)::int                     AS order_hour,
    CASE
        WHEN EXTRACT(HOUR FROM f.order_time) <= 7  THEN '1_00-07 overnight'
        WHEN EXTRACT(HOUR FROM f.order_time) <= 10 THEN '2_08-10 morning'
        WHEN EXTRACT(HOUR FROM f.order_time) <= 14 THEN '3_11-14 midday'
        WHEN EXTRACT(HOUR FROM f.order_time) <= 16 THEN '4_15-16 afternoon'
        WHEN EXTRACT(HOUR FROM f.order_time) <= 18 THEN '5_17-18 early evening'
        WHEN EXTRACT(HOUR FROM f.order_time) <= 21 THEN '6_19-21 evening peak'
        ELSE                                                  '7_22-23 late evening'
    END                                                      AS hour_band,
    (EXTRACT(HOUR FROM f.order_time) >= 17)::int             AS is_peak_hour,
    f.prep_time_minutes,
    f.delivery_time_minutes,
    f.sla_threshold_minutes,
    (f.delivery_time_minutes > f.sla_threshold_minutes)::int AS breach_flag,
    GREATEST(f.delivery_time_minutes - f.sla_threshold_minutes, 0) AS minutes_over_sla,
    c.category_name                                          AS category,
    wt.traffic,
    wt.weather,
    a.area_name                                              AS area,
    v.vehicle_name                                           AS vehicle,
    CASE WHEN ag.agent_rating_valid_flag THEN ag.agent_rating END                AS agent_rating,
    CASE WHEN ag.agent_rating_valid_flag THEN (ag.agent_rating < 4.5)::int END   AS rating_lt_4_5,
    ag.agent_age,
    (ag.agent_age >= 30)::int                                AS age_ge_30,
    f.distance_km
FROM routeiq."FactDelivery"      f
JOIN routeiq."DimDate"           d  ON d.date_key            = f.date_key
JOIN routeiq."DimCategory"       c  ON c.category_key        = f.category_key
JOIN routeiq."DimWeatherTraffic" wt ON wt.weather_traffic_key = f.weather_traffic_key
JOIN routeiq."DimArea"           a  ON a.area_key            = f.area_key
JOIN routeiq."DimVehicle"        v  ON v.vehicle_key         = f.vehicle_key
JOIN routeiq."DimAgent"          ag ON ag.agent_key          = f.agent_key;

COMMENT ON VIEW routeiq.vw_analytical_deliveries IS
    'Controlled analytical dataset: one row per delivery with every derived feature defined once (docs/data_dictionary.md).';
