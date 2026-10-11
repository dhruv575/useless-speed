# Public-folder verification

Checked on October 10, 2026 (Pacific time), after reorganizing the project into the standalone repository root.

- A clean root `npm ci` succeeded; root workspace commands build and run the renamed app.
- All eight model tests passed.
- TypeScript and the production Vite build passed.
- All 546 fingerprinted data artifacts matched their recorded sizes and SHA-256 hashes.
- All 223 cataloged source files and 760 timing-page pointers passed the corpus validator.
- SQLite integrity was `ok`; the sample Ocean Avenue search returned 211 full-text matches.
- The offline catalog rendered and filtered successfully in isolated headless Chromium without page errors.
- The catalog-inspection and compact-layer examples ran. The historical month/hour example produced 693 mapped features with no unmatched geometry, agreeing with the app snapshot within its two-decimal rounding.
- Headless Chrome passed address selection, routing, playback, pause/resume, rounded car timers, arrivals, settings reset, zero-speed equality, pin placement and mobile layout checks.
- Pin dragging, invalid-route rejection, routing-error retry and blocked-map-provider fallback passed.
- Relative documentation links were checked against the assembled folder.
- An initial Windows clone exposed excessive archived filename lengths. Those filenames and their catalog/SQLite references were shortened while all original-source hashes remained unchanged; the mapping is recorded in `corpus/metadata/path-aliases.json`.

Detailed corpus results are in `corpus/derived/validation.json`. Application browser reports are generated in ignored `app/test-output/` when the documented commands run.

These checks establish packaging, byte integrity and software behavior. They do not establish current signal plans, real-trip calibration or personal crash risk. Docker and a hosted Railway deployment have not been executed here; Docker was unavailable on the verification machine. The deployment recipe must be verified on its target platform.
