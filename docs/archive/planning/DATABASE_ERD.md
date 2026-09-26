# Database ER Diagram — RouteIQ Phase 2

Generated: 2026-08-16

This diagram reflects the **actually implemented** PostgreSQL schema in
the `routeiq` schema, verified against live `information_schema` /
`pg_constraint` output in `reports/sql_schema_validation.md`. Every
relationship shown below corresponds to a real, enforced foreign key —
none is aspirational or planned-but-not-built.

All relationships are one-to-many, dimension → fact, matching
`STAR_SCHEMA.md`'s documented cardinality (each delivery has exactly one
agent-attribute combination, one date, one area, one category, one
weather/traffic combination, one vehicle).

```mermaid
erDiagram
    DimAgent ||--o{ FactDelivery : "agent_key"
    DimDate ||--o{ FactDelivery : "date_key"
    DimArea ||--o{ FactDelivery : "area_key"
    DimCategory ||--o{ FactDelivery : "category_key"
    DimWeatherTraffic ||--o{ FactDelivery : "weather_traffic_key"
    DimVehicle ||--o{ FactDelivery : "vehicle_key"

    DimAgent {
        integer agent_key PK
        smallint agent_age
        boolean agent_age_valid_flag
        numeric agent_rating "nullable"
        boolean agent_rating_valid_flag
    }

    DimDate {
        integer date_key PK
        date full_date
        varchar day_of_week
        boolean is_weekend
        smallint week_number
        smallint month
    }

    DimArea {
        integer area_key PK
        varchar area_name
        boolean area_tier_valid_flag
    }

    DimCategory {
        integer category_key PK
        varchar category_name
    }

    DimVehicle {
        integer vehicle_key PK
        varchar vehicle_name
    }

    DimWeatherTraffic {
        integer weather_traffic_key PK
        varchar weather
        varchar traffic
    }

    FactDelivery {
        bigint delivery_key PK
        varchar order_id "unique, source traceability only"
        integer agent_key FK
        integer date_key FK
        integer area_key FK
        integer category_key FK
        integer weather_traffic_key FK
        integer vehicle_key FK
        time order_time
        time pickup_time
        smallint delivery_time_minutes
        smallint prep_time_minutes
        double distance_km "nullable"
        double sla_threshold_minutes "frozen, from sla_reference.csv"
        boolean sla_breach_flag
        boolean is_weekend
        smallint week_number
        boolean agent_rating_available_flag
        boolean coordinates_valid_flag
    }
```

## Notes

- **`DimAgent` is an attribute-derived dimension, not a true agent
  entity.** The diagram's `agent_key` PK is a technical surrogate for a
  distinct `(agent_age, agent_rating)` combination — there is no source
  `Agent_ID`, and this relationship must not be read as "each delivery
  belongs to one individual agent" in the way the other five relationships
  genuinely represent a real-world attribute of the order.
- **`DimWeatherTraffic` is a single combined dimension**, per
  `STAR_SCHEMA.md`'s documented design decision — this diagram does not
  show separate Weather/Traffic dimensions because none were built.
- **No snowflaking.** Every dimension joins directly to `FactDelivery`;
  no dimension references another dimension, matching `STAR_SCHEMA.md`'s
  "star, not snowflake" design philosophy.
- **Cardinality:** every relationship is `||--o{` (exactly one dimension
  row to zero-or-more fact rows) — in practice every dimension row that
  exists has at least one fact row, since dimensions were populated by
  `SELECT DISTINCT` over the same rows loaded into `FactDelivery`.
