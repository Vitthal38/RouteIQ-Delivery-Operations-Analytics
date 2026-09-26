-- =============================================================================
-- Q29 - Logistic-regression-ready feature set (the controlled model input)
-- Business question: what is the exact population and encoding behind the driver model?
-- One row per delivery with the 0/1 outcome and one-hot columns (reference levels:
-- traffic=Low, weather=Sunny, area=Metropolitian, vehicle=motorcycle).
-- Population: complete cases, EXCLUDING Semi-Urban (n=152, all breach -> complete separation,
-- reported descriptively instead) and the 54 rows with no valid rating.
-- Expected: 43,442 rows, 10,165 events. The Python model (src/routeiq/modeling) reads the same
-- definitions; tests/test_reconciliation.py compares row counts, events and column sums.
-- =============================================================================
SET search_path TO routeiq, public;

SELECT
    order_id,
    order_date,
    breach_flag                              AS y,
    (traffic = 'High')::int                  AS traffic_high,
    (traffic = 'Jam')::int                   AS traffic_jam,
    (traffic = 'Medium')::int                AS traffic_medium,
    (weather = 'Cloudy')::int                AS weather_cloudy,
    (weather = 'Fog')::int                   AS weather_fog,
    (weather = 'Sandstorms')::int            AS weather_sandstorms,
    (weather = 'Stormy')::int                AS weather_stormy,
    (weather = 'Windy')::int                 AS weather_windy,
    (area = 'Other')::int                    AS area_other,
    (area = 'Urban')::int                    AS area_urban,
    (vehicle = 'scooter')::int               AS vehicle_scooter,
    (vehicle = 'van')::int                   AS vehicle_van,
    rating_lt_4_5,
    age_ge_30,
    prep_time_minutes / 5.0                  AS prep_per_5min,
    hour_band
FROM routeiq.vw_analytical_deliveries
WHERE area <> 'Semi-Urban'
  AND rating_lt_4_5 IS NOT NULL
ORDER BY order_id;
