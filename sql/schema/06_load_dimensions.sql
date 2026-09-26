-- =============================================================================
-- 06_load_dimensions.sql — RouteIQ Phase 2
-- Stages the two frozen Phase 1 CSV outputs, then populates all six
-- dimensions from the staged cleaned dataset. FactDelivery is loaded
-- separately in 07_load_fact.sql, after every dimension row it needs to
-- reference already exists.
--
-- Required invocation (psql variables carry the absolute file paths — no
-- path is hardcoded inside this script; -f is required, not -c, since
-- plain-SQL variable substitution is only applied to script-file input):
--   psql -U postgres \
--        -v cleaned_csv="C:/Data Analyst Projects/RouteIQ Project/data/cleaned/cleaned_delivery.csv" \
--        -v sla_csv="C:/Data Analyst Projects/RouteIQ Project/data/cleaned/sla_reference.csv" \
--        -f 06_load_dimensions.sql
--
-- Loading uses server-side COPY, not the client-side \copy meta-command:
-- \copy's own argument parser does not reliably expand psql's quoted-literal
-- variable substitution (:'var'), verified during this build. Server-side
-- COPY is ordinary SQL text, which psql substitutes correctly when read via
-- -f. This requires the PostgreSQL server process itself to have read
-- access to the CSV path (confirmed working for this project's local
-- install) — if run against a server without that access, fall back to
-- \copy with the path written out literally instead of via variable.
--
-- Run as: see invocation above (psql -v ... -f 06_load_dimensions.sql)
-- =============================================================================

SET search_path TO routeiq, public;

-- -----------------------------------------------------------------------------
-- Staging tables — column order matches the CSV header order exactly (COPY
-- maps positionally, not by name). Types are chosen to accept the data
-- as-written by the Phase 1 Python pipeline without lossy conversion.
-- These are transient working tables, dropped and recreated on every run.
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS routeiq.stg_cleaned_delivery;
CREATE TABLE routeiq.stg_cleaned_delivery (
    "Order_ID"                      VARCHAR(20),
    "Agent_Age"                     SMALLINT,
    "Agent_Rating"                  NUMERIC(2,1),
    "Store_Latitude"                DOUBLE PRECISION,
    "Store_Longitude"               DOUBLE PRECISION,
    "Drop_Latitude"                 DOUBLE PRECISION,
    "Drop_Longitude"                DOUBLE PRECISION,
    "Order_Date"                    DATE,
    "Order_Time"                    TIME,
    "Pickup_Time"                   TIME,
    "Weather"                       VARCHAR(20),
    "Traffic"                       VARCHAR(10),
    "Vehicle"                       VARCHAR(20),
    "Area"                          VARCHAR(20),
    "Delivery_Time"                 SMALLINT,
    "Category"                      VARCHAR(30),
    agent_rating_available_flag     BOOLEAN,
    agent_rating_valid_flag         BOOLEAN,
    agent_age_valid_flag            BOOLEAN,
    coordinates_valid_flag          BOOLEAN,
    area_tier_valid_flag            BOOLEAN,
    distance_km                     DOUBLE PRECISION,
    sla_threshold_minutes           DOUBLE PRECISION,
    sla_breach_flag                 BOOLEAN,
    delivery_bucket                 VARCHAR(20),   -- staged only; not part of any documented dim/fact table
    day_of_week                     VARCHAR(9),
    is_weekend                      BOOLEAN,
    order_hour                      SMALLINT,       -- staged only; not part of any documented dim/fact table
    week_number                     SMALLINT,
    prep_time_minutes               SMALLINT
);

DROP TABLE IF EXISTS routeiq.stg_sla_reference;
CREATE TABLE routeiq.stg_sla_reference (
    "Category"               VARCHAR(30),
    row_count                INTEGER,
    sla_threshold_minutes    DOUBLE PRECISION
);

COPY routeiq.stg_cleaned_delivery FROM :'cleaned_csv' WITH (FORMAT csv, HEADER true);
COPY routeiq.stg_sla_reference FROM :'sla_csv' WITH (FORMAT csv, HEADER true);

-- -----------------------------------------------------------------------------
-- DimDate — one row per distinct Order_Date observed (44 expected).
-- day_of_week / is_weekend / week_number are pure functions of the date and
-- are carried over from the Phase 1-computed staging values rather than
-- re-derived, avoiding a second, potentially divergent implementation.
-- month has no Phase 1 column (not a documented FEATURE_ENGINEERING.md
-- field) and is derived here by plain calendar arithmetic on full_date.
-- -----------------------------------------------------------------------------
INSERT INTO routeiq."DimDate" (date_key, full_date, day_of_week, is_weekend, week_number, month)
SELECT DISTINCT
    TO_CHAR("Order_Date", 'YYYYMMDD')::INTEGER,
    "Order_Date",
    day_of_week,
    is_weekend,
    week_number,
    EXTRACT(MONTH FROM "Order_Date")::SMALLINT
FROM routeiq.stg_cleaned_delivery;

-- -----------------------------------------------------------------------------
-- DimArea — one row per distinct Area value (4 expected: Urban,
-- Metropolitian, Semi-Urban, Other). area_tier_valid_flag is a pure
-- function of Area (false only for 'Other').
-- -----------------------------------------------------------------------------
INSERT INTO routeiq."DimArea" (area_name, area_tier_valid_flag)
SELECT DISTINCT "Area", area_tier_valid_flag
FROM routeiq.stg_cleaned_delivery;

-- -----------------------------------------------------------------------------
-- DimCategory — one row per distinct Category (16 expected).
-- -----------------------------------------------------------------------------
INSERT INTO routeiq."DimCategory" (category_name)
SELECT DISTINCT "Category"
FROM routeiq.stg_cleaned_delivery;

-- -----------------------------------------------------------------------------
-- DimVehicle — one row per distinct Vehicle value actually present.
-- Expected 3 (motorcycle, scooter, van) — see 02_create_dimensions.sql
-- comment on the 0-bicycle-rows finding.
-- -----------------------------------------------------------------------------
INSERT INTO routeiq."DimVehicle" (vehicle_name)
SELECT DISTINCT "Vehicle"
FROM routeiq.stg_cleaned_delivery;

-- -----------------------------------------------------------------------------
-- DimWeatherTraffic — one row per distinct (Weather, Traffic) combination
-- actually observed (24 expected: all 6 x 4 combinations occur in the data).
-- -----------------------------------------------------------------------------
INSERT INTO routeiq."DimWeatherTraffic" (weather, traffic)
SELECT DISTINCT "Weather", "Traffic"
FROM routeiq.stg_cleaned_delivery;

-- -----------------------------------------------------------------------------
-- DimAgent — one row per distinct (Agent_Age, Agent_Rating) combination
-- (444 expected). agent_age_valid_flag / agent_rating_valid_flag are pure
-- functions of Agent_Age / Agent_Rating respectively, so including them in
-- the SELECT DISTINCT does not create extra rows beyond the 444 distinct
-- attribute pairs. NULLS NOT DISTINCT on the table's UNIQUE constraint
-- (02_create_dimensions.sql) ensures every (age, NULL rating) combination
-- collapses into a single row rather than one row per source order.
-- -----------------------------------------------------------------------------
INSERT INTO routeiq."DimAgent" (agent_age, agent_age_valid_flag, agent_rating, agent_rating_valid_flag)
SELECT DISTINCT "Agent_Age", agent_age_valid_flag, "Agent_Rating", agent_rating_valid_flag
FROM routeiq.stg_cleaned_delivery;
