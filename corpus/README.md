# San Francisco signal and traffic research corpus

Part of [Useless Speed](../README.md). For installation and current reproduction commands, see [the reproduction guide](../docs/reproducing.md).

Collected with isolated, headless Chrome on October 10, 2026 (Pacific time). No new public-records requests were submitted. Start with [the offline searchable catalog](index.html).

## What is here

- **160 unique source files** across 223 successful source records; 63 byte-identical duplicates are marked, not counted twice in search.
- **12,934 PDF pages**, with **460 candidate pages containing labeled timing** and 760 pages with timing/model mentions. These are pages, not distinct intersections or verified operating plans.
- Original PDF timing cards, three timing-workbook variants, Synchro 12 and SimTraffic files, signal drawings/CAD, and transportation-study appendices.
- SFCTA speed observations: **1,571,371 hourly segment records**, **132,940 peak-period segment records**, and historical corridor observations from **1991–2025**. Monthly data spans **January 2019–September 2026**; availability differs by segment and month.
- Citywide signal inventory, speed-limit segments, lane and one-way geometry, green-wave locations, and SFMTA traffic counts.
- Original-source URLs, SHA-256 hashes, byte sizes, retrieval timestamps, download failures, machine-readable page candidates, and a full-text SQLite index.

The retained selected originals occupy 2.14 GB (1.51 GB unique content). This public bundle includes selected cataloged originals; exploratory downloads are not included. Use the catalog rather than raw file counts for coverage.

## Best starting points

| Evidence | What it establishes |
|---|---|
| [Checked timing-card subset](derived/verified_timing_cards.json) | Dated settings for 19th/Sloat (2015 existing plus a separate 2014 draft), 3rd/25th (2024), and 41st/Chain of Lakes/Lincoln (2025). Four source documents, three intersections. |
| [Checked plan rows](derived/verified_timing_plans.csv) | Small manual subset of cycles, offsets, schedule/mode, revision date, source page, and caveats. |
| [All timing candidate pages](derived/timing_pages.csv) | Jump to labeled values and Synchro pages. Includes modeled existing, future, and project scenarios. |
| [Full file catalog](derived/catalog.csv) | Source URL, file path, hash, category, duplicate relationship. |
| [Structured catalog](derived/catalog.json) | Adds extraction method, PDF/sheet counts, schema and record counts. |
| [SQLite full-text database](derived/corpus.sqlite) | Search extracted PDF pages, workbook sheets and relevant correspondence. |

For example, the 2015 19th/Sloat card contains 100- and 120-second schedules with offsets. The 2024 3rd/25th card contains 120-second coordinated plans, FREE periods, transit priority, and preemption. The 2025 41st/Lincoln card specifies isolated FREE operation and nightly FLASH. These examples already show why a universal fixed-red-light model would be inadequate.

## Data snapshots

| Dataset | Records/features | Source period, when provided |
|---|---:|---|
| [Intersection Counts 2014 - 2022](raw/supporting/2112858b600a__Intersection_Counts_2014_-_2022.csv) | 1,189 | – |
| [Corridor Counts 2014 - 2022](raw/supporting/f1e820f3e440__Corridor_Counts_2014_-_2022.csv) | 8,099 | – |
| [signal_inventory](raw/supporting/6645796981a6__signal_inventory.geojson) | 1,507 | – |
| [speed_limits](raw/supporting/f99016dc492c__speed_limits.geojson) | 16,083 | – |
| [traffic_lanes](raw/supporting/84e14ce771f2__traffic_lanes.geojson) | 15,444 | – |
| [one_way_streets](raw/supporting/16315a30959e__one_way_streets.geojson) | 3,810 | – |
| [greenwave_signals](raw/supporting/e94eb54ddab0__greenwave_signals.geojson) | 47 | – |
| [greenwave_streets](raw/supporting/b305d8706fc1__greenwave_streets.geojson) | 63 | – |
| [SFCTA cmp_segments_master](raw/sfcta/cmp_segments_master.json) | 245 | – |
| [SFCTA cmp_autotransit](raw/sfcta/cmp_autotransit.json) | 4,855 | 1991–2017 |
| [SFCTA cmp_autotransit_xd](raw/sfcta/cmp_autotransit_xd.json) | 2,936 | 2017–2025 |
| [SFCTA cmp_aggregate](raw/sfcta/cmp_aggregate.json) | 99 | 2006–2025 |
| [SFCTA cmp_aggregate_xd](raw/sfcta/cmp_aggregate_xd.json) | 144 | 2017–2025 |
| [SFCTA cmp_segments_exp](raw/sfcta/cmp_segments_exp.json) | 740 | – |
| [SFCTA inrix_rt_weekly_exp](raw/sfcta/inrix_rt_weekly_exp.json) | 132,940 | 2019-01–2026-09 |
| [SFCTA inrix_rt_weekly_exp_agg](raw/sfcta/inrix_rt_weekly_exp_agg.json) | 930 | 2019-01–2026-09 |
| [SFCTA inrix_rt_hourly_exp_agg](raw/sfcta/inrix_rt_hourly_exp_agg.json) | 4,464 | 2019-01–2026-09 |
| [SFCTA inrix_rt_hourly_exp](raw/sfcta/inrix_rt_hourly_exp.json) | 1,571,371 | 2019-01–2026-09 |

Raw JSON/GeoJSON is retained. Tabular UTF-8 exports are in [derived/tables](derived/tables). GIS schemas and coded-value domains are archived alongside the original data. Geometry remains available in GeoJSON; a CSV geometry column is serialized JSON.

## Coverage and interpretation

This is **not a verified current citywide cycle/offset database**. Timing cards are dated agency records. Engineering designs can be drafts. Transportation reports contain scenario assumptions, and repeated intersections across AM/PM, future years, and alternatives. A reference to a timing card is not itself the card.

Automatically extracted cycle and offset values are **candidates**. Each retains its verbatim line and PDF page. No automatic join asserts that an extracted number belongs to a particular current controller. Actuated cycle length in a model is distinguished from nominal cycle length. Blank offsets and FREE are not converted to zero. Only the small checked subset has been manually reviewed.

15 primary-card pages have local OCR, with bounding boxes and confidence scores in [derived/ocr](derived/ocr). 1,639 other PDF pages have sparse text and no OCR; many are maps, images, or scans. Native CAD, Synchro/SimTraffic, and archive files are preserved but have not been simulated or decoded into controller settings. ZIPs are inventoried without expansion. Workbook extraction retains formulas and cached values without recalculating them.

The SFCTA `inrix_rt_weekly_exp` endpoint is the **monthly dashboard's** underlying table despite its name. Its `year` field is 2020 throughout this snapshot while `date` spans 2019–2026; use `date` and preserve that source anomaly. The hourly table has month/date, hour period, segment ID, and mean speed—not vehicle trajectories or second-by-second light states. Dashboard labels give speeds in mph. Aggregates overlap their underlying observations and should not be added as independent measurements.

Testing the original speeding/red-light hypothesis would still require a route model: signal sequence, offsets/reference phases, time-of-day plans, actuation/priority behavior, queues, acceleration, and matched departure times. This corpus supplies useful inputs and observed-speed context, but does not itself measure a causal travel-time benefit from speeding.

## Collection method and limits

1. Searched public NextRequest document titles using ten timing/model/traffic terms and searched request descriptions. Expanded narrowly relevant requests and downloaded technical attachments. Search-result and request metadata are retained under `metadata/`; those discovery records are not all relevant corpus files.
2. Scanned all **50 pages / 492 entries** of the SF Planning environmental-review library. Downloaded transportation attachments and selected bundled appendices. For retired `sfmea`, `archives`, and `default` hosts, resolved public files in SF Planning's S3 archive and recorded the successful URL.
3. Read public ArcGIS layer directories and downloaded every feature, verifying returned feature counts against the layer count endpoint.
4. Captured SFCTA dashboard network requests and downloaded the exposed data. Returned row counts were checked against HTTP Content-Range totals.
5. Preserved originals, checked file signatures, hashed files, extracted text/cells, identified duplicates, indexed pages, and visually inspected representative primary timing cards.

The corpus includes selected historical plans for 19th Avenue, 41st/Lincoln, 3rd/25th, and other intersections; reports cover Better Market Street, Stonestown, Balboa Reservoir, the Hub, India Basin, Potrero Power Station, Central SoMa and additional areas. Spatial coverage is uneven.

See [failed downloads](metadata/failures.json). Six Planning shared links reported an expired or invalid link; an older duplicate SFMTA count link returned 404 while its current replacement downloaded successfully. Some SFCTA main-site pages required browser security verification, but the public dashboards and their data endpoints worked. NextRequest request `26-9464` attachment pagination stopped after 100 metadata records with server errors; `25-131` also returned an attachment-list server error. These are recorded gaps, not evidence that records do not exist. No comprehensive citywide operational SPaT feed was established by this collection.

## Use and reproduce

Open `index.html` directly; it embeds the catalog and works offline. The browser search covers titles, scenario cues, and timing excerpts. For complete extracted text, run:

```powershell
python corpus/scripts/query.py 'Synchro AND Existing'
python corpus/scripts/query.py '"Ocean Avenue"' --limit 20
python corpus/scripts/query.py '"signal timing"' --json
```

The database has `documents` and FTS5 `pages` tables. Page numbers are one-based PDF pages; workbook results use sheet sequence numbers. Document hashes join the text, page, workbook and OCR artifacts.

Collection scripts use public requests inside an isolated Playwright Chromium context with `headless=True`. They do not use your Chrome profile. Key scripts:

```powershell
python -m venv .venv
# Activate it, then install corpus/requirements.txt and Playwright Chromium.
python corpus/scripts/collect_curated.py
python corpus/scripts/collect_planning.py
python corpus/scripts/download_planning.py
python corpus/scripts/collect_supporting.py
python corpus/scripts/probe_dashboards.py
python corpus/scripts/collect_speeds.py
python corpus/scripts/ocr_cards.py
python corpus/scripts/build_index.py
python corpus/scripts/verified_cards.py
python corpus/scripts/publish_catalog.py
```

Existing metadata/downloads are reused. To update discovery rather than reproduce this snapshot, review the saved search/query lists and website pagination; future endpoints and document links can change. `collect_curated.py` uses the archived global searches as its starting catalog. Download manifests and relevant public discovery metadata are retained for provenance; transient logs and website response bodies are omitted.

## Primary portals

- [San Francisco public records archive](https://sanfrancisco.nextrequest.com/documents)
- [41st/Lincoln public request 25-2143](https://sanfrancisco.nextrequest.com/requests/25-2143)
- [19th Avenue public request 22-3290](https://sanfrancisco.nextrequest.com/requests/22-3290)
- [3rd/25th public request 25-1486](https://sanfrancisco.nextrequest.com/requests/25-1486)
- [SF Planning environmental review library](https://sfplanning.org/environmental-review-documents)
- [SFMTA traffic counts](https://www.sfmta.com/TrafficCounts)
- [SFMTA traffic GIS layers](https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer)
- [SFCTA congestion dashboard](https://congestion.sfcta.org/)
- [SFCTA Congestion Management Program dashboard](https://cmp.sfcta.org/)
