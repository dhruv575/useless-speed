import type { Comparison, Run } from "./types";
import { riskIndex, sampleAt } from "./simulation";

// Compare only distance both vehicles have covered. In-flight moving time is
// integrated from saved traces; exact whole-trip metrics appear upon arrival.
function movingTimeline(run: Run) {
  const cumulative = [0];
  for (let i = 1; i < run.samples.length; i++) {
    const a = run.samples[i - 1],
      b = run.samples[i];
    let fraction = 1;
    if (a.v < 0.3 && b.v < 0.3) fraction = 0;
    else if (a.v < 0.3) fraction = (b.v - 0.3) / (b.v - a.v);
    else if (b.v < 0.3) fraction = (a.v - 0.3) / (a.v - b.v);
    cumulative.push(cumulative[i - 1] + (b.t - a.t) * fraction);
  }
  return (t: number) => {
    if (t >= run.duration) return run.movingSeconds;
    let low = 0,
      high = run.samples.length - 1;
    while (low < high) {
      const mid = Math.ceil((low + high) / 2);
      if (run.samples[mid].t <= t) low = mid;
      else high = mid - 1;
    }
    const next = Math.min(low + 1, run.samples.length - 1);
    const f =
      (t - run.samples[low].t) /
      (run.samples[next].t - run.samples[low].t || 1);
    return cumulative[low] + (cumulative[next] - cumulative[low]) * f;
  };
}
function timeAtDistance(run: Run, distance: number, now: number) {
  const current = sampleAt(run, now);
  // A lead is erased while both cars wait at the same stop.
  if (Math.abs(current.s - distance) < 0.5) return Math.min(now, run.duration);
  let low = 0,
    high = run.samples.length - 1;
  while (low < high) {
    const mid = Math.ceil((low + high) / 2);
    if (run.samples[mid].s <= distance) low = mid;
    else high = mid - 1;
  }
  const a = run.samples[low],
    b = run.samples[Math.min(low + 1, run.samples.length - 1)];
  return Math.min(
    now,
    a.t + ((b.t - a.t) * (distance - a.s)) / (b.s - a.s || 1),
  );
}
export function liveComparison(comparison: Comparison) {
  const movingA = movingTimeline(comparison.baseline),
    movingB = movingTimeline(comparison.faster);
  return (time: number) => {
    if (
      time >= Math.max(comparison.baseline.duration, comparison.faster.duration)
    )
      return comparison;
    const shared = Math.min(
      sampleAt(comparison.baseline, time).s,
      sampleAt(comparison.faster, time).s,
    );
    if (shared < 1)
      return {
        movingGainPct: 0,
        timeSavedPct: 0,
        injuryRiskPct: 0,
        fatalRiskPct: 0,
      };
    const ta = timeAtDistance(comparison.baseline, shared, time),
      tb = timeAtDistance(comparison.faster, shared, time);
    const ma = movingA(ta),
      mb = movingB(tb),
      ratio = mb > 0.01 ? ma / mb : 1;
    const risk = riskIndex(ratio);
    return {
      movingGainPct: (ratio - 1) * 100,
      timeSavedPct: ta > 0.01 ? ((ta - tb) / ta) * 100 : 0,
      injuryRiskPct: risk.injury,
      fatalRiskPct: risk.fatal,
    };
  };
}
