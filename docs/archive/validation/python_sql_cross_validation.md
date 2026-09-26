# Python ↔ SQL Cross-Validation Report — RouteIQ Phase 4

Generated: 2026-08-16

Every Python figure below was computed fresh from `data/cleaned/cleaned_delivery.csv`
in `python/analysis/05_cross_validation.py` — none is copied from any SQL
report text. Every SQL figure is quoted from `reports/sql_analysis_validation.md`
(Phase 3, already approved). This is an independent reproduction, not a
restatement.

**Result: 0 discrepancies. No value required investigation; no SQL or
Python output was altered to force a match.**

---

## Core row-count and SLA KPIs

| Metric | SQL (Phase 3) | Python (Phase 4) | Match |
|---|---|---|---|
| Total deliveries | 43,648 | 43,648 | ✅ |
| Distinct `Order_ID` | 43,648 | 43,648 | ✅ |
| Total SLA breaches | 10,328 | 10,328 | ✅ |
| Overall breach rate | 23.6620% | 23.6620% | ✅ |
| Every category has exactly one SLA threshold | Yes (16/16) | Yes (16/16, `sla_threshold_category_has_single_value = True`) | ✅ |

## Breach rate by area

| Area | SQL | Python | Match |
|---|---|---|---|
| Metropolitian | 26.5000% | 26.5000% | ✅ |
| Urban | 14.3738% | 14.3738% | ✅ |
| Semi-Urban | 100.0000% | 100.0000% | ✅ |
| Other | 11.4437% | 11.4437% | ✅ |

## Category row counts (16/16)

| Category | SQL n | Python n | Match |
|---|---|---|---|
| Electronics | 2,843 | 2,843 | ✅ |
| Books | 2,817 | 2,817 | ✅ |
| Jewelry | 2,796 | 2,796 | ✅ |
| Toys | 2,773 | 2,773 | ✅ |
| Snacks | 2,767 | 2,767 | ✅ |
| Skincare | 2,766 | 2,766 | ✅ |
| Outdoors | 2,741 | 2,741 | ✅ |
| Apparel | 2,722 | 2,722 | ✅ |
| Sports | 2,711 | 2,711 | ✅ |
| Grocery | 2,688 | 2,688 | ✅ |
| Pet Supplies | 2,684 | 2,684 | ✅ |
| Home | 2,680 | 2,680 | ✅ |
| Cosmetics | 2,670 | 2,670 | ✅ |
| Kitchen | 2,667 | 2,667 | ✅ |
| Clothing | 2,662 | 2,662 | ✅ |
| Shoes | 2,661 | 2,661 | ✅ |

## Vehicle, weather, and traffic counts

| Dimension | Segment | SQL n | Python n | Match |
|---|---|---|---|---|
| Vehicle | motorcycle | 25,519 | 25,519 | ✅ |
| Vehicle | scooter | 14,607 | 14,607 | ✅ |
| Vehicle | van | 3,522 | 3,522 | ✅ |
| Weather | Fog | 7,440 | 7,440 | ✅ |
| Weather | Stormy | 7,374 | 7,374 | ✅ |
| Weather | Cloudy | 7,288 | 7,288 | ✅ |
| Weather | Sandstorms | 7,245 | 7,245 | ✅ |
| Weather | Windy | 7,223 | 7,223 | ✅ |
| Weather | Sunny | 7,078 | 7,078 | ✅ |
| Traffic | Low | 14,999 | 14,999 | ✅ |
| Traffic | Jam | 13,725 | 13,725 | ✅ |
| Traffic | Medium | 10,628 | 10,628 | ✅ |
| Traffic | High | 4,296 | 4,296 | ✅ |

## Weekday / weekend

| Metric | SQL | Python | Match |
|---|---|---|---|
| Weekday count | 31,627 | 31,627 | ✅ |
| Weekend count | 12,021 | 12,021 | ✅ |
| Weekday avg delivery time | 124.90 min | 124.8960 min | ✅ (SQL rounded to 2dp) |
| Weekend avg delivery time | 124.96 min | 124.9631 min | ✅ (SQL rounded to 2dp) |

## Breach count by weather

| Weather | SQL | Python | Match |
|---|---|---|---|
| Fog | 2,756 | 2,756 | ✅ |
| Cloudy | 2,650 | 2,650 | ✅ |
| Windy | 1,449 | 1,449 | ✅ |
| Stormy | 1,406 | 1,406 | ✅ |
| Sandstorms | 1,381 | 1,381 | ✅ |
| Sunny | 686 | 686 | ✅ |

## Correlation coefficients (Q04 / Q10 / Q15)

| Correlation | SQL `CORR()` | Python `pearsonr` | n | Match |
|---|---|---|---|---|
| Agent rating vs. delivery time | -0.3077 | -0.3077 | 43,594 | ✅ |
| Distance vs. delivery time | 0.2781 | 0.2781 | 39,997 | ✅ |
| Agent age vs. delivery time | 0.2585 | 0.2585 | 43,594 | ✅ |
| Agent age vs. agent rating | -0.1176 | -0.1176 | 43,594 | ✅ |

## Validity-flag row counts

| Flag | SQL | Python | Match |
|---|---|---|---|
| `coordinates_valid_flag = true` | 39,997 | 39,997 | ✅ |
| `agent_rating_valid_flag = true` | 43,594 | 43,594 | ✅ |

---

## Discrepancies found

**None.** Every figure matched to the precision reported by both layers
(SQL rounds to 2 or 4 decimal places depending on the query; Python's
higher-precision values round to the identical SQL figure in every case —
this is a rounding-display difference, not a calculation difference, and
is noted here rather than silently reconciled).

No value in this report was adjusted, rounded differently, or recalculated
to force a match — every number above is the first result each layer
produced.
