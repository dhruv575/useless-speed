# Reproducing and extending the corpus

There are three different tasks: verify the archived snapshot, rebuild derived outputs from it, or collect newer source material. Keep them separate. Source sites can change, remove files or return different bytes; running a collector later is not guaranteed to reproduce this snapshot.

## 1. Verify the existing snapshot

From the repository root, with Git LFS and Python 3.11+ installed:

```sh
git lfs pull
python tools/verify_snapshot.py
```

This streams SHA-256 hashes without loading every large file into memory. It also checks that the original-source catalog agrees with the snapshot manifest. `--available` permits absent/LFS-only research artifacts and reports how many it skipped; app data remains required. It does not turn a partial checkout into a verified full corpus.

`corpus/derived/validation.json` is the historical collection validation report. `app/QA.md` records application checks. Their dates and scope matter; a stored report is not proof that a later edit was tested.

## 2. Set up Python for collection and extraction

The examples and SQLite search need only the standard library. Collection, PDF/spreadsheet extraction and OCR need the additional packages. Python 3.11 was used for the recorded environment.

```sh
python -m venv .venv
```

Activate the environment:

```sh
# macOS / Linux / Git Bash
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then install the recorded package versions and the browser:

```sh
python -m pip install -r corpus/requirements.txt
python -m playwright install chromium
```

On a Linux machine missing browser system libraries, use `python -m playwright install --with-deps chromium` with the permissions appropriate to that machine. The collection scripts in this distribution use isolated, headless Playwright Chromium. The original collection used installed headless Chrome; the engine/channel change makes a clean machine easier to set up, but can affect site behavior. No user browser profile or account is required by the collectors.

The requirements file is the original full environment freeze, including OCR dependencies. Platform-specific wheel availability may differ. A newer dependency environment is a new reproduction environment: record it rather than silently changing the original lock information.

## 3. Rebuild derived files from the archived originals

Work in a branch or a separate clone. These commands **overwrite generated indexes and catalogs**; preserve the checked-in snapshot if you need exact byte comparisons later.

```sh
python corpus/scripts/ocr_cards.py
python corpus/scripts/build_index.py
python corpus/scripts/verified_cards.py
python corpus/scripts/publish_catalog.py
python corpus/scripts/validate_corpus.py
```

| Script | Behavior |
|---|---|
| `ocr_cards.py` | OCRs eligible sparse pages in primary timing cards; reuses existing OCR outputs |
| `build_index.py` | Reads selected successful download manifests, identifies duplicates, extracts PDFs/workbooks/tables, and rebuilds SQLite and timing-page candidates |
| `verified_cards.py` | Re-emits the **previously reviewed, hardcoded** four-card subset; it does not perform new human verification |
| `publish_catalog.py` | Rebuilds `corpus/index.html` and **`corpus/README.md`**, leaving the repository's main README untouched |
| `validate_corpus.py` | Checks original hashes, row counts, page pointers and SQLite, then tests the local catalog in headless Chromium |

Extracted page caches are keyed by source hash. Updating extraction logic while keeping those caches will reuse the old extraction. Use a separate output copy or deliberately clear only the affected generated artifacts when testing a new extractor. Never overwrite an original record to fix an extraction mistake.

Rebuilding changes generated timestamps and can change extraction bytes across library versions. The snapshot manifest intentionally detects those changes. For a new release, review the differences, create a new dated manifest from the verified outputs, and update the coverage and environment documentation. Do not overwrite the old manifest simply to hide an unexplained mismatch.

## 4. Collect newer public records

The collectors encode a particular discovery strategy and known portal behavior. Review their query lists and site pagination before refreshing. They use cached metadata/download manifests and are not a universal, automatic "update everything" command.

| Stage | Command from repository root | Inputs/output |
|---|---|---|
| Broad NextRequest discovery | `python corpus/scripts/collect_nextrequest.py discover` | Searches document titles and request descriptions; writes catalog/search metadata |
| Focused request collection | `python corpus/scripts/collect_curated.py` | Uses discovery catalog and selected requests; downloads relevant public attachments |
| Planning discovery | `python corpus/scripts/collect_planning.py` | Records the environmental-review library and project attachments |
| Planning downloads | `python corpus/scripts/download_planning.py` | Resolves selected report/appendix links, including archived hosts |
| Supporting source discovery | `python corpus/scripts/discover_sources.py` | Captures public portal pages and layer directories, including count links |
| GIS/count downloads | `python corpus/scripts/collect_supporting.py` | Reads discovery metadata; retrieves features, schemas and counts |
| Dashboard endpoint discovery | `python corpus/scripts/probe_dashboards.py` | Records public dashboard response URLs; may also capture temporary response bodies |
| SFCTA table collection | `python corpus/scripts/collect_speeds.py` | Downloads discovered data endpoints and records row totals/date ranges |

Successful manifest entries are often skipped on rerun. To refresh a dataset, archive its existing original and manifest first, then explicitly reset that selected entry in a new working copy. Some scripts also cache request/discovery pages. Neither deleting only the original nor blindly rerunning every script is a reliable refresh procedure.

The checked-in `metadata/dashboard_network/*_network.json` contains only the public SFCTA API discovery entries needed for collection. Website script bodies, screenshots and unrelated network responses were omitted from the public package. A new probe may regenerate them; review outputs before committing.

Known original gaps include expired Planning links and NextRequest attachment-list failures/truncated pagination. The original Planning scan covered 50 pages / 492 entries, which is a description of that scan, not a guarantee about future site totals. See the collection notes and `metadata/failures.json`.

After collecting, rerun extraction and validation, inspect changed counts and source hashes, and review timing candidates against the actual documents. Do not automatically merge future/project assumptions into an operational signal plan.

## 5. Rebuild the app's compact datasets

```sh
python corpus/scripts/prepare_simulator_data.py
```

This reads supporting GIS manifests, SFCTA hourly observations and expanded geometry. It writes compact files to `app/public/data/`, selecting the latest available observation month, and records provenance. It also downloads the address directory, stop signs, and demo route **only when the corresponding local files are absent**. The app is already shipped with these snapshots, so rebuilding them is not required to run it.

The preparer can contact public services even when most files are cached. Run it deliberately in a separate working copy if preserving the original release is important. Verify geographic bounds, counts, schemas, sentinel filters and time units before accepting a refresh. Its browser is isolated and headless.

## 6. Verify application behavior

```sh
npm ci
npm test
npm run build
```

For the existing optional UI checks, start `npm start` in another terminal and install Playwright plus Chrome (`python -m playwright install chrome`) if Chrome is not already available. The app QA scripts intentionally use `channel='chrome'` with an isolated headless context:

```sh
python app/qa_browser.py
python app/qa_resilience.py
```

They contact the map/routing services and can fail during an external outage. They write ignored reports and screenshots to `app/test-output/`. They test UI behavior and model invariants, not real-world accuracy. The research validator uses bundled Chromium as described above.
