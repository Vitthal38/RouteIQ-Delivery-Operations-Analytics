-- =============================================================================
-- 02_create_dimensions.sql — RouteIQ Phase 2
-- Creates the six dimension tables exactly as specified in STAR_SCHEMA.md.
--
-- Naming: table names use quoted PascalCase ("DimAgent", not dimagent) to
-- preserve STAR_SCHEMA.md's documented naming standard verbatim — that
-- document states PascalCase table names are chosen specifically for
-- Power BI's default relationship-detection behavior, so folding to
-- lowercase (PostgreSQL's default for unquoted identifiers) would silently
-- undo that intent. Column names are snake_case, matching STAR_SCHEMA.md,
-- and are left unquoted (snake_case already survives PostgreSQL's
-- lowercase-folding unchanged).
--
-- Grain of every dimension: one row per DISTINCT combination of its
-- documented attributes as observed in data/cleaned/cleaned_delivery.csv.
-- No row is invented for a combination that does not appear in the data.
--
-- Run as: psql -U postgres -f 02_create_dimensions.sql
-- =============================================================================

SET search_path TO routeiq, public;

-- -----------------------------------------------------------------------------
-- DimDate
-- Built only from the 44 distinct Order_Date values actually observed in the
-- cleaned dataset (2022-02-11 to 2022-04-06) — not padded to a full calendar
-- year. STAR_SCHEMA.md's "Future Scalability" section notes full-range
-- padding as a hypothetical production enhancement, not a current requirement.
-- -----------------------------------------------------------------------------
CREATE TABLE routeiq."DimDate" (
    date_key      INTEGER      PRIMARY KEY,       -- YYYYMMDD, per STAR_SCHEMA.md
    full_date     DATE         NOT NULL UNIQUE,    -- source: Order_Date
    day_of_week   VARCHAR(9)   NOT NULL,           -- source: day_of_week (e.g. 'Wednesday')
    is_weekend    BOOLEAN      NOT NULL,           -- source: is_weekend
    week_number   SMALLINT     NOT NULL,           -- source: week_number (ISO week)
    month         SMALLINT     NOT NULL            -- derived from full_date (1-12)
);

COMMENT ON TABLE routeiq."DimDate" IS
    'Standard date dimension, covering only the observed 2022-02-11 to '
    '2022-04-06 range (44 rows), per STAR_SCHEMA.md > DimDate.';

-- -----------------------------------------------------------------------------
-- DimArea
-- -----------------------------------------------------------------------------
CREATE TABLE routeiq."DimArea" (
    area_key              SERIAL       PRIMARY KEY,
    area_name             VARCHAR(20)  NOT NULL UNIQUE,  -- source: Area (cleaned, trimmed)
    area_tier_valid_flag  BOOLEAN      NOT NULL          -- False only for 'Other', per Cleaning Step 8
);

COMMENT ON TABLE routeiq."DimArea" IS
    'Delivery area dimension. area_name preserves the source spelling '
    '"Metropolitian" verbatim per DATA_CLEANING_PLAN.md Step 9 — display-label '
    'correction to "Metropolitan" is a presentation-layer concern, not a '
    'stored-data change. "Other" is retained (area_tier_valid_flag = false), '
    'never dropped, per DATA_CLEANING_PLAN.md Step 8.';

-- -----------------------------------------------------------------------------
-- DimCategory
-- -----------------------------------------------------------------------------
CREATE TABLE routeiq."DimCategory" (
    category_key    SERIAL       PRIMARY KEY,
    category_name   VARCHAR(30)  NOT NULL UNIQUE   -- source: Category
);

COMMENT ON TABLE routeiq."DimCategory" IS
    'Product category dimension. 16 categories expected, per '
    'DATA_PROFILING_PLAN.md and the frozen sla_reference.csv.';

-- -----------------------------------------------------------------------------
-- DimVehicle
-- -----------------------------------------------------------------------------
CREATE TABLE routeiq."DimVehicle" (
    vehicle_key    SERIAL       PRIMARY KEY,
    vehicle_name   VARCHAR(20)  NOT NULL UNIQUE   -- source: Vehicle
);

COMMENT ON TABLE routeiq."DimVehicle" IS
    'Delivery vehicle dimension, populated only from vehicle values actually '
    'present in the cleaned dataset. NOTE: raw data documented 4 vehicle '
    'types including "bicycle" (15 rows), but all 15 bicycle rows fell '
    'inside the Cleaning Step 3 91-row exclusion cluster (missing '
    'Weather/Traffic) — 0 bicycle rows remain post-cleaning, so this '
    'dimension has 3 rows (motorcycle, scooter, van), not 4. See '
    'reports/sql_schema_validation.md for the full finding.';

-- -----------------------------------------------------------------------------
-- DimWeatherTraffic (combined dimension, per STAR_SCHEMA.md design decision —
-- NOT split into separate Weather/Traffic dimensions)
-- -----------------------------------------------------------------------------
CREATE TABLE routeiq."DimWeatherTraffic" (
    weather_traffic_key   SERIAL       PRIMARY KEY,
    weather               VARCHAR(20)  NOT NULL,   -- source: Weather (cleaned)
    traffic               VARCHAR(10)  NOT NULL,   -- source: Traffic (cleaned, NaN-recoded)
    UNIQUE (weather, traffic)
);

COMMENT ON TABLE routeiq."DimWeatherTraffic" IS
    'Combined Weather x Traffic dimension per STAR_SCHEMA.md''s documented '
    'design decision (the two fields are always observed together for a '
    'given delivery, and the primary root-cause business questions analyze '
    'the combination, not each field independently). Populated only from '
    'the 24 combinations actually observed — no combination is invented.';

-- -----------------------------------------------------------------------------
-- DimAgent — ATTRIBUTE-DERIVED DIMENSION, NOT A TRUE AGENT ENTITY.
--
-- The source dataset contains no Agent_ID. agent_key is a technical
-- surrogate key generated for each distinct (agent_age, agent_rating)
-- attribute combination observed in the cleaned dataset — it does NOT
-- identify a real individual delivery agent, and must never be presented,
-- joined, or narrated as if it did (no longitudinal per-agent performance
-- tracking is possible from this data). This limitation is stated
-- explicitly in STAR_SCHEMA.md's DimAgent design decision and is preserved
-- here without exception.
--
-- agent_rating is nullable (54 true-null rows retained per Cleaning Step 5).
-- NULLS NOT DISTINCT (PostgreSQL 15+) ensures every row sharing the same
-- agent_age with a NULL agent_rating collapses into a single dimension row,
-- rather than the ordinary SQL rule where every NULL is treated as distinct.
-- -----------------------------------------------------------------------------
CREATE TABLE routeiq."DimAgent" (
    agent_key                SERIAL        PRIMARY KEY,
    agent_age                SMALLINT      NOT NULL,   -- source: Agent_Age
    agent_age_valid_flag     BOOLEAN       NOT NULL,   -- Cleaning Step 6 (18-65 bound)
    agent_rating              NUMERIC(2,1),             -- source: Agent_Rating; nullable
    agent_rating_valid_flag  BOOLEAN       NOT NULL,   -- Cleaning Steps 4-5 (range + null)
    UNIQUE NULLS NOT DISTINCT (agent_age, agent_rating)
);

COMMENT ON TABLE routeiq."DimAgent" IS
    'ATTRIBUTE-DERIVED DIMENSION — NOT A TRUE AGENT ENTITY. The source '
    'dataset has no Agent_ID; agent_key is a technical surrogate for a '
    'distinct (agent_age, agent_rating) combination only, per STAR_SCHEMA.md''s '
    'explicit design decision. Do not interpret agent_key as an individual '
    'delivery agent identifier or use it for per-agent longitudinal analysis.';

COMMENT ON COLUMN routeiq."DimAgent".agent_key IS
    'Technical surrogate key for a (agent_age, agent_rating) combination. '
    'NOT an agent identifier — no real Agent_ID exists in the source data.';
