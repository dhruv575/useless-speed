# Verification — compact sidebar

The redesign replaces the full-height sidebar and bottom dashboard with one compact floating panel. It starts with empty address placeholders, four time icons, a 20% default slider, one simulation button and four initially empty result boxes. The model's caveats are available on hover and keyboard focus.

The latest pass distinguishes target cruising speed above the limit from actual average moving-speed increase, places section and result titles above their controls and values, and uses a two-column result grid. A locally customized OpenFreeMap Positron vector style replaces the raster map with muted colors and less clutter. Address inputs disable autocapitalization; typed casing is retained, all-caps city address records display in lowercase, and map labels have no uppercase transform.

Two compact boxes, **Time car 1** and **Time car 2**, show elapsed simulated time rounded to the nearest minute, including time stopped. They start empty, advance with playback, pause with playback, freeze at each car's arrival and clear when settings change. Percentage calculations retain full precision.

## Functional verification

- Production TypeScript/Vite build passed.
- Eight model tests passed, including zero-speed equality, no red-light crossings across 30 departure phases, and live metrics that do not reveal unearned future speed gains.
- Headless Chrome verified address search, keyboard time selection, route calculation, live values, pause/resume, both arrivals, replay-ready state, settings invalidation, pin placement, and mobile layout without horizontal overflow.
- Production vector-map assets loaded with attribution and without browser errors.
- Headless checks confirmed exact speed labels, preserved typed casing, disabled autocapitalization, and titles above values at desktop and mobile widths.
- Elapsed car timers passed whole-minute formatting, advance, pause, reset, zero-speed equality and arrival checks.
- Pin dragging, invalid endpoint rejection, routing-error retry and blocked-tile fallback passed.

Latest reports: `test-output/minimal-report.json` and `test-output/resilience-report.json`. Screenshots are prefixed `minimal-`. Reports from the original dashboard are historical and do not describe the current interface.

## UI polish

No actionable UI-polish findings remain in the inspected desktop and mobile layouts. The check covers default, filled, selected, loading, disabled, paused, running, finished and error states, and hidden model details on focus. Static labels and selected icon backgrounds accompany animation states. Button press scale remains 0.96; transitions name their properties and use 120 ms durations. Reduced-motion styles suppress these transitions.

Not verified: physical touchscreen behavior or a full screen-reader audit. No coverage is claimed for those checks.

Approve for the inspected UI states.

## Scientific scope

The slider controls target cruising speed; the first box reports achieved mean moving-speed increase over the route distance both cars have covered. Final whole-trip metrics replace the live estimates when both arrive. These checks validate software behavior, not city traffic calibration or personal crash probability. See [README.md](README.md) for the unchanged model limitations.
