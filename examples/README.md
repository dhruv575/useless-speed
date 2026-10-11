# Examples

Run these from the repository root with Python 3.11+. They use only the standard library and leave source snapshots unchanged. Generated exports go to the ignored `outputs/` directory.

| Command | Result | Needs Git LFS data? |
|---|---|---|
| `python examples/inspect_corpus.py` | Counts, evidence categories, checked intersections and one source record | No |
| `python examples/compact_map.py --output outputs/signals.geojson` | 1,305 prepared signal locations | No |
| `python examples/compact_map.py --dataset observed-speeds --hour 17 --output outputs/evening.geojson` | September 2026 speed observations with a `speed_mph` field | No |
| `python examples/hourly_speeds.py --month 2026-09 --hour 17` | Historical CSV observations joined to SFCTA geometry | Yes: SFCTA geometry and the hourly CSV |
| `python corpus/scripts/query.py 'Synchro AND Existing' --limit 10` | Ranked full-text matches and original page references | Yes: SQLite index |

Open exported GeoJSON in QGIS or load it as a source in MapLibre. Coordinates are longitude, latitude in WGS84. Hour selections refer to the source dashboard's local-hour bins, not an individual timestamped trip. See the [data dictionary](../docs/data-dictionary.md) before joining identifiers or interpreting speed values.

To fetch only the historical example's required large files:

```sh
git lfs pull --include="corpus/raw/sfcta/cmp_segments_exp.json,corpus/derived/tables/inrix_rt_hourly_exp.csv"
```
