# Contributing

Useful contributions include corrected source transcriptions, additional dated signal cards, validated joins, better traffic modeling, reproducible examples and accessible UI improvements.

## Code

Use Node 24, run `npm ci`, then `npm test` and `npm run build`. Keep the interface compact, use sentence case, preserve typed address casing, and place field/card titles above their values. Document any change to simulation assumptions or risk formulas in `app/README.md`. Keep the simulator independent of the large research files.

## Data and evidence

For a new source, preserve the original bytes and record its public URL, collection timestamp, byte count, SHA-256, agency/document title and meaningful source/revision dates. Retain an existing record instead of replacing it with a newer plan. Put large research artifacts under the LFS-managed corpus paths.

For a timing claim, include the original page, intersection, movement/phase, schedule, mode, scenario, units and offset reference where available. Distinguish a proposed design or model input from an implemented setting. A machine candidate or OCR transcription is not a reviewed fact. Explain exactly what was checked if adding to the reviewed subset; update `corpus/scripts/verified_cards.py` as well as its generated outputs.

Keep null/blank/FREE/FLASH values meaningful. Never infer a missing offset as zero or join unrelated identifier systems by string coincidence. Quantify missing coverage and duplicate observations. Preserve source attribution and applicable licenses when publishing derived data.

## Validation

Run `python tools/verify_snapshot.py` before changing data to establish the baseline. After a deliberate snapshot update, review and document changed originals, artifacts, counts and dates before issuing a new snapshot manifest. The old manifest should identify changes; do not mechanically regenerate it to make unexplained failures disappear.

Use `python corpus/scripts/validate_corpus.py` for full corpus/index/catalog validation after setting up its Python/browser dependencies. The small examples and `--available` integrity check run in CI without downloading the full research collection. Optional application browser checks are described in `docs/reproducing.md`.

When reporting a problem, include the command, environment, file or document ID, and expected/actual behavior. For source corrections, include the public page link and evidence. Do not include credentials or private browser profiles in reports.
