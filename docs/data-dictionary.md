# Data dictionary

Use this guide with the original agency schemas and source pages. Field names and unit conventions vary by dataset; no universal intersection/segment identifier spans the entire corpus.

## Catalog and provenance

`corpus/derived/catalog.json` is an array of 223 successful source records. `catalog.csv` is its flatter export. Failed records are separate in `corpus/metadata/failures.json`.

| Field | Meaning |
|---|---|
| `id` | String record ID; NextRequest document ID or a provider-prefixed ID |
| `title`, `category` | Source title and collection classification, not an assertion that a plan is current |
| `source_url` | Public original/landing/API URL |
| `resolved_download_url` | Successful underlying download URL, when recorded |
| `retrieved_at` | UTC collection timestamp; distinct from observation/revision date |
| `local_path` | Original file path relative to `corpus/` |
| `bytes`, `sha256` | Exact archived file size and SHA-256 |
| `duplicate_of` | ID of the first byte-identical source record, or null |
| `text_path`, `workbook_path` | Derived artifact path relative to `corpus/`, when available |
| `extraction` | Method, page/sheet counts, sparse-page/OCR counts or row/field information |
| `row_count`, `feature_count`, `expected_count`, `content_range` | Observed and source-reported coverage checks, where applicable |
| `date_min/max`, `year_min/max` | Source field range, where captured; not a guarantee of continuous coverage |

Extraction files use the first 20 characters of the source SHA-256 as their filename stem. The full hash remains in the catalog. `snapshot-manifest.json` additionally fingerprints 546 bundled source/derived/app-data files using repository-root-relative paths. It excludes regenerated validation reports and preview images.

The source collection includes duplicates intentionally. Use `duplicate_of is null` for unique-file counts. Do not deduplicate observations just because they share a document or a segment ID.

## Timing evidence

`corpus/derived/timing_pages.json` contains machine-discovered candidate pages:

| Field | Meaning |
|---|---|
| `document_id`, `pdf_page` | Source join and one-based PDF page; for indexed workbooks, a sheet sequence |
| `heading_candidates`, `scenario_context` | Extracted intersection headings and existing/future/AM/PM cues |
| `cycle_length_seconds_candidates` | Verbatim numeric strings following nominal cycle labels |
| `actuated_cycle_seconds_candidates` | Separately retained actuated-cycle labels |
| `offset_seconds_candidates` | Verbatim numeric strings; reference phase/time is not inferred |
| `verbatim_timing_lines`, `snippets` | Context for a human to check |
| `strength` | `labeled_timing` or `timing_mention`; not a confidence score or approval |
| `machine_ocr` | Whether the text used on that page came from machine OCR |

`verified_timing_cards.json` is the limited reviewed subset, with nested `plans`; `verified_timing_plans.csv` flattens one row per plan. The card fields include intersection, optional `cnn`, document/page/hash, revision, status and notes. Plan fields include `cso`, `cycle_seconds`, `offset_seconds`, `schedule` and optional `mode`. Preserve null values. `FREE` means uncoordinated/actuated operation and `FLASH` is a distinct operating mode. Neither supplies a conventional fixed cycle. An offset without its reference is incomplete information.

Only four documents at three intersections were checked. The 2014 Sloat draft and 2015 existing card are separate evidence; change numbers are not a reliable chronological sequence. None proves that the settings remain active today.

## SFCTA traffic observations

All files below are under `corpus/raw/sfcta/`; CSV exports use the same stem under `corpus/derived/tables/`.

| File | Rows | Key / content |
|---|---:|---|
| `inrix_rt_hourly_exp.json` | 1,571,371 | `cmp_segid`, `date`, `period`, `avg_speed` |
| `inrix_rt_weekly_exp.json` | 132,940 | Expanded segment/month/AM-PM observations and comparison fields |
| `cmp_segments_exp.json` | 740 | Expanded segment geometry and directional descriptions |
| `inrix_rt_hourly_exp_agg.json` | 4,464 | Aggregates overlapping hourly observations |
| `inrix_rt_weekly_exp_agg.json` | 930 | Aggregates overlapping peak-period observations |
| `cmp_segments_master.json` | 245 | Earlier CMP segment system |
| `cmp_autotransit.json` | 4,855 | Earlier corridor observations, 1991–2017 |
| `cmp_autotransit_xd.json` | 2,936 | Later observations, 2017–2025 |
| `cmp_aggregate.json` | 99 | Earlier aggregate series, 2006–2025 |
| `cmp_aggregate_xd.json` | 144 | Later aggregate series, 2017–2025 |

For the hourly table:

- `cmp_segid`: segment ID. Normalize to a consistent string/integer type before joining.
- `date`: `YYYY-MM`; monthly source period, not the timestamp of a single trip.
- `period`: string hour bin, normally `"0"`–`"23"`; strip whitespace and parse as an integer.
- `avg_speed`: mean speed in mph according to the dashboard labels. Missing is not zero. These observations include intersection delay.

For expanded geometry, `cmp_segid` joins to the speed table. `geometry` is itself a JSON-encoded GeoJSON string in the archived rows: parse it once before mapping. `cmp_name`, `cmp_from`, `cmp_to` and `direction` identify the corridor section. Preserve the source `length` field but verify its convention before using it for distance-weighting; it is not used by the provided export example.

Despite its name, `inrix_rt_weekly_exp` underlies the monthly dashboard. Its `period` is AM/PM, not an hour. Its `year` is 2020 throughout this snapshot even though `date` spans 2019–2026. Fields such as `base_speed`, `imp_vol`, `pct_diff` and `los_hcm85` are source-specific outputs; inspect the dashboard methodology before interpreting them. Avoid casual joins between the master and expanded segment systems, or across network revisions.

The [historical example](../examples/hourly_speeds.py) demonstrates a month/hour join without inventing missing observations, averaging segment means, or combining overlapping aggregates.

## SFMTA GIS and counts

`corpus/raw/supporting/` contains hashed source filenames. Find a layer by title in the catalog instead of hardcoding the hash. The matching `*_schema.json` record preserves field types, descriptions, aliases and coded-value domains.

| Layer/title | Features | Interpretation |
|---|---:|---|
| `signal_inventory` | 1,507 | All retained raw signal-related features, including types excluded by the app |
| `speed_limits` | 16,083 | Raw limit features; 0/99 are not ordinary posted limits |
| `traffic_lanes` | 15,444 | Street geometry and classification |
| `one_way_streets` | 3,810 | Directional context; not a finished routable graph |
| `greenwave_signals` / `greenwave_streets` | 47 / 63 | Published green-wave locations; no inferred live coordination schedule |
| Intersection / corridor counts | 1,189 / 8,099 | Source CSV tables; period and approach conventions are in their headers/source context |

GIS downloads explicitly requested `outSR=4326`: coordinates are longitude, latitude in degrees. Do not compute metric distances directly in degrees. Use an appropriate projection or geodesic distance. The simulator performs its own distance/alignment matching.

`OBJECTID` is a layer/snapshot identifier. `CNN` identifies a street or intersection reference in the relevant layer; it is not interchangeable with SFCTA `cmp_segid`. Treat it as a string when joining and verify whether the record describes an intersection or a segment. Blank strings, nulls and coded status fields should retain their source meaning. ArcGIS date fields can be epoch milliseconds, as specified by the archived schema.

## App-ready snapshots

`app/public/data/` uses smaller property sets; the original records remain in the corpus where applicable.

| File | Important properties |
|---|---|
| `signals.json` | `id`, string `cnn`, `name`, `system`, source `actuated`, source `priority` |
| `speed-limits.json` | `id`, `cnn`, `name`, `limit` in mph, `status`, `school`, `installed` |
| `streets.json` | `name`, source road `class` |
| `observed-speeds.json` | `id` = expanded `cmp_segid`, `name`, `direction`, `speeds` mapping hour strings to mph; collection-level `period` |
| `stop-signs.json` | Original layer-10 properties; consult `app/data/stop-sign-schema.json` |

`app/data/addresses.json` contains `eas_address_id`, `address`, longitude/latitude (source numeric strings), optional landmark fields and neighborhood. It is the server's search directory, not a list of residents. The API filters coordinates to the app's SF bounds and returns up to seven deduplicated suggestions. Source field definitions are archived in `corpus/metadata/address_schema.json`.

`app/data/places.json` is a separate ODbL-licensed OpenStreetMap supplement with 14,305 named destinations. `id` is `osm:<node|way|relation>:<id>`; `label` is the source name; `coordinates` is `[longitude, latitude]`; `kind` is `place`; `category` is a readable source tag; `address` may be empty; `aliases` preserves alternative names. Ways and relations use bounding-box centers, not verified entrances. The source date, query, bounds, license and file hash are in `app/data/places-provenance.json`. Search also derives named landmark suggestions from the official address directory. Its combined response uses `kind` = `address`, `landmark` or `place`, and excludes internal search keys and aliases. Names are not evidence that a business remains open.

The supplemental stop-sign source is SFMTA Traffic FeatureServer layer 10; the address source is SF Enterprise Addressing System dataset `3mea-di5p`. The source URLs, preparation logic and source schemas should accompany derived exports. `app/data/demo-route.json` is a saved route fixture, not an observed trip.

## SQLite, workbooks and OCR

The database schema is:

```sql
documents(id, title, category, path, source_url, sha256, duplicate_of)
pages(document_id, page, text) -- SQLite FTS5; first two fields UNINDEXED
```

`derived/pages/<hash-prefix>.json` contains extraction metadata and page text. `derived/workbooks/<hash-prefix>.json` contains sheets and sparse cell records with `cell`, `value_or_formula` and `cached_value`. Formulas were not recalculated; a cached value may be stale or absent. CSV exports encode list/object cells as JSON and use UTF-8, often with a BOM (`utf-8-sig` in Python).

OCR records include source hash, one-based page, method, text, and blocks with bounding boxes and confidence values. OCR confidence is not verification of timing semantics. The current 15-page OCR subset is narrow; the remaining sparse pages need separate review.
