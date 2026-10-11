# Useless Speed

A local, top-down San Francisco driving experiment built on the traffic corpus in `../corpus/`. It compares two independent cars on one shared route: one targets the speed limit, and the other targets 0–100% above it. Playback runs at 60 simulated seconds per real second.

**This is an exploratory simulator, not a validated city traffic model.** We have useful traffic observations and signal documents, but do not yet have a complete, current, movement-specific operating plan for every intersection. The interface identifies assumptions instead of presenting them as measured signal behavior.

## Run

Requires Node.js 22.12+ (tested with 24.19) and the included data snapshots.

```powershell
cd useless-speed
npm install
npm run dev
```

Open **http://127.0.0.1:5481**. The local API runs on port 8788. Both listen only on the local machine.

For the production build:

```powershell
npm run build
npm start
```

Then open **http://127.0.0.1:8788**. The development command also starts this API; do not start another server on the same port.

## Use

1. Enter a street address or place name and select a suggestion, or use the pin icons to click the map. Existing pins can be dragged. Search runs locally against 224,402 official SF address records, their landmark names, and 14,305 OpenStreetMap destinations such as cafés, parks and attractions. It does not request your device location or call a geocoder as you type.
2. Use the four time icons for morning (08:00), midday (12:00), evening (17:00), or night (22:00).
3. Set Car 2's target excess speed, which defaults to **20%**. Both cars take the same route and leave together.
4. Select **Simulate**. The same button pauses, resumes, or replays the run. Playback runs at 60x.
5. **Time car 1** and **Time car 2** show elapsed simulated time rounded to the nearest minute, including stops. Each timer freezes at that car's arrival. Percentage calculations retain full precision. Four initially empty percentage boxes update during the drive and finalize on arrival. Hover or focus a percentage box for its definition and model caveats.

The compact interface has no bottom dashboard, introductory copy, timeline, or export control. Map attribution is retained. New routes require network access unless cached. The saved sample route remains a data fixture at `/api/demo`, but is not loaded into the interface automatically. Map tiles and optional Google Fonts require network access; local street geometry and system fonts provide fallbacks.

### Target speed versus achieved speed

The slider is labeled **Car 2 target cruising speed above the limit (%)**. The first result is **Car 2 actual average moving-speed increase (%)**: it compares Car 2 with Car 1, excluding standing still. Acceleration, turns and braking usually make the achieved increase smaller than the target. A 20% setting means a 30 mph target on a 25 mph road; it does not mean the average speed of the full drive will be 20% higher.

Section and result titles sit above their controls and values. Result cards use a compact two-column grid. Address inputs preserve typed casing, disable browser autocapitalization and autocorrection, and display the city's all-caps address records in lowercase. Map labels retain their source casing without uppercase styling.

During playback, all four metrics compare the route portion both cars have covered. Moving time is integrated from the saved trajectories, and time savings use the time each car took to reach the shared distance. A lead disappears while both cars wait at the same stop. Final values use the engine's whole-trip metrics. No final result is presented before the simulation runs.

## Data used

| Input           | Snapshot / source                                                                                                                 | Use and limit                                                                                                             |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Addresses       | [SF Enterprise Addressing System](https://data.sf.gov/d/3mea-di5p), 224,402 rows                                                  | Local lookup. Bounds cover the SF peninsula and nearby city islands, not SFO or all SF-owned land.                        |
| Signals         | [SFMTA layer 7](https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer/7), 1,305 installed signal features | Location matching. Pending signals and beacons excluded.                                                                  |
| Speed limits    | [SFMTA layer 9](https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer/9), 3,754 non-sentinel segments     | Nearest aligned segment within 25 m. Values 0 and 99 excluded. Snapshot coverage is not proof of the current legal limit. |
| Stop signs      | [SFMTA layer 10](https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer/10), 11,179 records                | Street-name/proximity approach matching; incomplete lane/direction reconstruction.                                        |
| Street geometry | SFMTA traffic-lanes snapshot in the parent corpus                                                                                 | Local map fallback.                                                                                                       |
| Traffic speeds  | [SFCTA Congestion Tracker](https://congestion.sfcta.org/), September 2026, 693 segments                                           | Hour-specific observed speeds; underlying 2019–2026 corpus retained separately.                                           |
| Driving routes  | [OSRM](https://project-osrm.org/) public demo / OpenStreetMap                                                                     | One route chosen for both cars. Route results are cached locally and new requests are spaced at least 1.1 seconds apart.  |
| Basemap         | [OpenFreeMap](https://openfreemap.org/) vector tiles / OpenStreetMap, rendered with MapLibre GL JS                                 | Customized light Positron style; normal on-screen requests with attribution.                                              |

Source snapshot metadata is in `public/data/provenance.json`. Preparation code is `../corpus/scripts/prepare_simulator_data.py`; it reads the existing corpus and uses isolated headless Chromium for the supplementary public downloads. Cached supplementary files are reused on reruns.

`ROUTER_URL` can replace the public OSRM server with another compatible service. The public routing demo is suitable for this local prototype; see the [OSRM demo policy](https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server).

The basemap is configured in `src/map-style.json`. It adapts [OpenFreeMap's Positron style](https://github.com/hyperknot/openfreemap-styles) with muted land and water, fewer labels and no uppercase text transform. Positron derives from OpenMapTiles and CartoDB Basemaps, designed by Stamen and Paul Norman for CartoDB Inc. Upstream license notices are retained in `public/map-style-license.md` and `public/positron-license.md`. There is no API key requirement. The old raster `VITE_TILE_URL` setting has been replaced by the local vector-style configuration. Local SFMTA street geometry remains the fallback if the vector provider fails.

`src/theme.ts` recolors the existing map layers for morning, midday, evening and night; `src/styles.css` provides matching interface tokens. Theme changes preserve the map instance, route and pins. Changing the departure time still clears previous simulation results so they cannot be mistaken for the new time.

Place search lives in `server/search.mjs`. It combines separate official-address and OSM indexes, ranks names/aliases and street addresses, handles accents, and collapses nearby duplicate names while retaining separate business branches. `data/places.json` is an ODbL snapshot with provenance in `data/places-provenance.json`; refresh it with `python corpus/scripts/prepare_places.py --refresh` from the repository root. Coverage and business status can be incomplete or stale. Park/building centers are not verified entrances; routing snaps them to roads.

## Model

The route is sampled at intervals of at most 9 m. The engine integrates at 0.2-second steps, separate from the animation clock, in a Web Worker. Cars accelerate at 1.65 m/s², anticipate lower speed limits and turns, and normally brake at up to 2.7 m/s². A stop-line guard can impose an abrupt stop when a signal changes near a crossing; this is a simplification, not a physical emergency-braking or collision model. Cars do not interact, follow queues, compete for lanes, or block one another. Hills, driver reaction differences, pedestrians, weather, incidents, and lane changes are absent.

Unmatched streets assume 25 mph; identified motorways assume 55 mph. School/conditional schedules are not applied. The prepared route retains coverage by distance; this is not shown in the compact sidebar. The router can include motorways and does not provide a verified street-only exclusion profile on its public demo. Inputs are geographically bounded and routes over 35 km are rejected.

Most signals assume a 90-second cycle, 40-second approach green, and deterministic synthetic offsets using the inventory's system grouping, location, and route approach. There is no claim that these offsets reconstruct SF's actual progression. The “green” model window excludes a 1.2-second end buffer, but there is no proper yellow/all-red or turn-phase model.

Two intersections can substitute historical cycle lengths:

- **19th/Sloat**, CNN 23149000: [2015 existing card](https://sanfrancisco.nextrequest.com/documents/16282596), 120 seconds from 06:30–22:00 and 100 seconds otherwise under the simplified weekday schedule. Its actual splits, offset reference, and actuation are not reconstructed.
- **3rd/25th**, CNN 23541000: [2024 card](https://sanfrancisco.nextrequest.com/documents/43475468), 120 seconds during the selected daytime hours. FREE operation at night is not reconstructed; the night model uses an explicitly assumed cycle.

The 41st/Lincoln FREE/FLASH card remains evidence in the corpus; it is not converted into a fabricated fixed-cycle operating plan. Other timing documents are not automatically applied until their intersection, date, scenario, phase references, and operating status are checked.

Stop signs have a two-second dwell. If at least 35% of the route has hourly speed observations, the engine computes an observed travel-time reference from the covered distance and extrapolates it over the route. It subtracts the mean baseline travel time from four signal-only runs and converts only a positive residual into a shared extra delay per control, capped at 12 seconds. At lights this becomes lost time at the start of green; at stop signs it adds dwell. This coarse adjustment **does not guarantee calibration to observed times**. It avoids charging the full observed intersection delay twice by treating observed mean speed as a cruising cap and adding signals again.

The engine retains departure sensitivity internally, although the compact UI does not display it. It uses 12 paired departures spaced 10 seconds apart over 110 seconds. Within each pair the cars see the same signal world. The range is sensitivity to departure timing under one assumed signal pattern, not a confidence interval or a range covering uncertainty in actual signal schedules.

## What each percentage means

- **Time saved** = 100 × (baseline duration − faster duration) / baseline duration.
- **Overall trip speed increase** = 100 × (baseline duration / faster duration − 1), since distance is equal. This differs from percent time saved.
- **Moving-speed increase** compares distance / moving time, excluding samples below 0.3 m/s. Acceleration, turns, and stops mean this usually differs from the target excess speed.
- **Injury-crash index** = 100 × (r^1.2 − 1).
- **Fatal-crash index** = 100 × (r^2.6 − 1).

For the last two, r is the ratio of simulated mean moving speeds. The exponents are the urban/residential estimates from [TØI report 1034/2009, summary Table S1](https://www.toi.no/getfile.php/Publikasjoner/T%C3%98I%20rapporter/2009/1034-2009/1034-2009-Sum.pdf). Their exponent intervals are 0.7–1.7 and 0.3–4.9, respectively. The comparison object also retains corresponding sensitivity ranges, which are **not validated individual-trip risk intervals**.

These are population-level speed–risk relationships applied illustratively. They do not establish the causal risk for a particular driver, personal crash probability, or risk on a specific SF trip. The urban relationship is not justified for freeway driving. Very large target increases extrapolate beyond a reliable local comparison. “Injury crash” excludes property-damage-only crashes; “fatal crash” concerns a crash involving a fatality, not specifically the driver's death. The [WHO road-safety overview](https://www.who.int/en/news-room/fact-sheets/detail/road-traffic-injuries) provides broader context on speed and severity.

## Validation

```powershell
npm test
npm run build
```

Eight model tests cover identical cars, free-flow travel-time bounds, red-light crossing across 30 departure phases, stop dwell, time accounting, playback bounds, risk equations, invalid settings, and live metrics without premature final results.

With the development server running, the existing corpus Python environment can execute headless Chrome checks:

```powershell
python app/qa_browser.py
```

This checks empty address placeholders, the 20% default, four time icons with keyboard navigation, local address selection and casing, clarified speed labels, titles above values, route calculation, live values, pause/resume, both arrivals, 0% equality, pin placement, model details on focus, and mobile layout. `qa_resilience.py` additionally checks invalid endpoints, pin dragging, routing-error retry, and the tile-provider fallback. Reports and screenshots go to `test-output/`. These checks validate software behavior, not predictive accuracy.

## Next steps toward a defensible city model

Reconstruct current movement-specific signal plans and their time-of-day schedules, validate route-level limits and stop approaches, and model queues/turn phases. Calibrate on held-out measured travel times or vehicle trajectories, rather than the same averages used for fitting. A traffic engine such as SUMO could replace the simplified independent-car model while keeping this interface, but signal and demand validation would still be necessary.
