-- =============================================================================
-- 03_create_fact.sql — RouteIQ Phase 2
-- Creates FactDelivery with exactly the 19 fields (delivery_key + order_id +
-- 6 FK keys + 11 measures/flags) documented in STAR_SCHEMA.md. No column
-- beyond this documented set is added.
--
-- Grain: ONE ROW = ONE DELIVERY ORDER (Order_ID). Verified unique in
-- data/cleaned/cleaned_delivery.csv (43,648 rows, 43,648 distinct Order_ID)
-- during the Step 1 pre-implementation audit.
--
-- Foreign-key constraints are added separately in 04_create_constraints.sql,
-- after both dimensions and fact tables exist.
--
-- Run as: psql -U postgres -f 03_create_fact.sql
-- =============================================================================

SET search_path TO routeiq, public;

CREATE TABLE routeiq."FactDelivery" (
    delivery_key                  BIGSERIAL     PRIMARY KEY,

    -- Source traceability (natural/business key, not used as a join key)
    order_id                      VARCHAR(20)   NOT NULL UNIQUE,

    -- Dimension foreign keys (constraints added in 04_create_constraints.sql)
    agent_key                     INTEGER       NOT NULL,
    date_key                      INTEGER       NOT NULL,
    area_key                      INTEGER       NOT NULL,
    category_key                  INTEGER       NOT NULL,
    weather_traffic_key           INTEGER       NOT NULL,
    vehicle_key                   INTEGER       NOT NULL,

    -- Degenerate time attributes (kept on fact; no separate time dimension,
    -- per STAR_SCHEMA.md)
    order_time                    TIME          NOT NULL,
    pickup_time                   TIME          NOT NULL,

    -- Core measures
    delivery_time_minutes         SMALLINT      NOT NULL
                                                 CHECK (delivery_time_minutes > 0),
    prep_time_minutes             SMALLINT      NOT NULL
                                                 CHECK (prep_time_minutes >= 0),
    distance_km                   DOUBLE PRECISION,   -- nullable: NULL when
                                                        -- coordinates_valid_flag = false

    -- Frozen SLA fields — sourced from data/cleaned/sla_reference.csv at
    -- load time (07_load_fact.sql), never recalculated here.
    sla_threshold_minutes         DOUBLE PRECISION NOT NULL,
    sla_breach_flag                BOOLEAN         NOT NULL,

    -- Engineered flags carried onto the fact row per STAR_SCHEMA.md
    is_weekend                    BOOLEAN       NOT NULL,
    week_number                   SMALLINT      NOT NULL,
    agent_rating_available_flag   BOOLEAN       NOT NULL,
    coordinates_valid_flag        BOOLEAN       NOT NULL
);

COMMENT ON TABLE routeiq."FactDelivery" IS
    'Grain: one row per delivery order (Order_ID). 19 documented fields per '
    'STAR_SCHEMA.md > FactDelivery — no additional column added. Loaded from '
    'data/cleaned/cleaned_delivery.csv (43,648 rows expected).';

COMMENT ON COLUMN routeiq."FactDelivery".order_id IS
    'Natural/business key retained for source traceability per STAR_SCHEMA.md '
    '> Keys. Not used as a join key — delivery_key is the surrogate PK.';

COMMENT ON COLUMN routeiq."FactDelivery".sla_threshold_minutes IS
    'Frozen category-level P75 of Delivery_Time, per SLA_METHODOLOGY.md. '
    'Sourced by JOIN to the loaded sla_reference.csv at fact-load time — '
    'never recalculated in SQL.';

COMMENT ON COLUMN routeiq."FactDelivery".sla_breach_flag IS
    'delivery_time_minutes > sla_threshold_minutes (strict greater-than; '
    'equality is on-time), computed once at load time against the frozen '
    'threshold. Enforced identically by a CHECK constraint added in '
    '04_create_constraints.sql.';

COMMENT ON COLUMN routeiq."FactDelivery".distance_km IS
    'Haversine distance; NULL for rows with coordinates_valid_flag = false '
    '(Cleaning Step 7), per FEATURE_ENGINEERING.md #1 edge case. Never '
    'defaulted to 0 or any placeholder.';
