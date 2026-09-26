-- =============================================================================
-- 04_create_constraints.sql — RouteIQ Phase 2
-- Adds the six documented FactDelivery -> Dim* foreign keys, plus CHECK
-- constraints that mechanically enforce already-documented business rules
-- (they encode rules already frozen in SLA_METHODOLOGY.md / FEATURE_ENGINEERING.md
-- — they do not introduce any new rule).
--
-- Run as: psql -U postgres -f 04_create_constraints.sql
-- =============================================================================

SET search_path TO routeiq, public;

-- -----------------------------------------------------------------------------
-- Foreign keys (STAR_SCHEMA.md > Relationships: one-to-many, dimension -> fact)
-- -----------------------------------------------------------------------------

ALTER TABLE routeiq."FactDelivery"
    ADD CONSTRAINT fk_fact_agent
    FOREIGN KEY (agent_key) REFERENCES routeiq."DimAgent" (agent_key);

ALTER TABLE routeiq."FactDelivery"
    ADD CONSTRAINT fk_fact_date
    FOREIGN KEY (date_key) REFERENCES routeiq."DimDate" (date_key);

ALTER TABLE routeiq."FactDelivery"
    ADD CONSTRAINT fk_fact_area
    FOREIGN KEY (area_key) REFERENCES routeiq."DimArea" (area_key);

ALTER TABLE routeiq."FactDelivery"
    ADD CONSTRAINT fk_fact_category
    FOREIGN KEY (category_key) REFERENCES routeiq."DimCategory" (category_key);

ALTER TABLE routeiq."FactDelivery"
    ADD CONSTRAINT fk_fact_weather_traffic
    FOREIGN KEY (weather_traffic_key) REFERENCES routeiq."DimWeatherTraffic" (weather_traffic_key);

ALTER TABLE routeiq."FactDelivery"
    ADD CONSTRAINT fk_fact_vehicle
    FOREIGN KEY (vehicle_key) REFERENCES routeiq."DimVehicle" (vehicle_key);

-- -----------------------------------------------------------------------------
-- CHECK constraints — mechanical enforcement of already-frozen rules
-- -----------------------------------------------------------------------------

-- SLA_METHODOLOGY.md Frozen SLA Definition: sla_breach_flag = 1 if
-- Delivery_Time > sla_threshold_minutes, strict greater-than, else 0.
-- This makes the boundary rule (equality = on-time) impossible to violate
-- at the database level, not just at load time.
ALTER TABLE routeiq."FactDelivery"
    ADD CONSTRAINT chk_sla_breach_flag_matches_rule
    CHECK (sla_breach_flag = (delivery_time_minutes > sla_threshold_minutes));

-- FEATURE_ENGINEERING.md #1 validation: "Result is always >= 0."
ALTER TABLE routeiq."FactDelivery"
    ADD CONSTRAINT chk_distance_km_non_negative
    CHECK (distance_km IS NULL OR distance_km >= 0);

-- FEATURE_ENGINEERING.md #1 edge case: distance_km is null/excluded exactly
-- for coordinate-invalid rows, never computed for them and never left null
-- for coordinate-valid rows.
ALTER TABLE routeiq."FactDelivery"
    ADD CONSTRAINT chk_distance_km_null_iff_coords_invalid
    CHECK (
        (coordinates_valid_flag = TRUE  AND distance_km IS NOT NULL) OR
        (coordinates_valid_flag = FALSE AND distance_km IS NULL)
    );
