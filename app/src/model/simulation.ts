import type { Comparison, Control, PreparedRoute, Run, Sample } from "./types";
export const MPH = 0.44704;
const STEP = 0.2,
  ACCEL = 1.65,
  BRAKE = 2.7;
const mod = (n: number, m: number) => ((n % m) + m) % m;
export function phase(
  control: Control,
  absoluteSeconds: number,
  perturbation = 0,
) {
  if (control.kind === "stop") return { green: false, position: 0 };
  const position = mod(
    absoluteSeconds - control.offset + perturbation,
    control.cycle,
  );
  return {
    green: position >= control.queue && position < control.green - 1.2,
    position,
  };
}
export function simulate(
  route: PreparedRoute,
  overspeed: number,
  departureShift = 0,
  queue = 0,
  save = true,
): Run {
  if (!Number.isFinite(overspeed) || overspeed < 0 || overspeed > 100)
    throw new Error("Overspeed must be 0–100%.");
  let s = 0,
    v = 0,
    t = 0,
    idx = 0,
    controlIndex = 0,
    stopIndex = -1,
    stopRelease = Infinity,
    moving = 0,
    stopped = 0,
    stops = 0,
    wasStopped = false,
    peak = 0;
  const samples: Sample[] = [
    { t: 0, s: 0, v: 0, waiting: false, limit: route.points[0].limit },
  ];
  while (s < route.length - 0.01 && t < 14400) {
    while (idx < route.points.length - 2 && route.points[idx + 1].s <= s) idx++;
    while (
      controlIndex < route.controls.length &&
      route.controls[controlIndex].s < s - 0.4
    ) {
      controlIndex++;
      stopIndex = -1;
      stopRelease = Infinity;
    }
    const current = route.points[idx];
    let target = current.limit * MPH * (1 + overspeed / 100);
    // Anticipate lower limits and turns, rather than teleporting between speeds.
    for (
      let k = idx + 1;
      k < route.points.length && route.points[k].s - s < 110;
      k++
    ) {
      const p = route.points[k],
        cap = p.limit * MPH * (1 + overspeed / 100);
      target = Math.min(
        target,
        Math.sqrt(cap * cap + 2 * BRAKE * Math.max(0, p.s - s)),
      );
    }
    for (const turn of route.turns) {
      const gap = turn.s - s;
      if (gap >= -7 && gap < 100)
        target = Math.min(
          target,
          Math.sqrt(turn.cap * turn.cap + 2 * BRAKE * Math.max(0, gap - 4)),
        );
    }
    // Both cars finish at rest at exactly the same snapped endpoint.
    target = Math.min(
      target,
      Math.sqrt(2 * BRAKE * Math.max(0, route.length - s)),
    );
    const control = route.controls[controlIndex];
    let blocked = false,
      gap = Infinity;
    if (control) {
      gap = Math.max(0, control.s - s);
      if (control.kind === "stop") {
        if (gap < 0.45 && v < 0.4 && stopIndex !== controlIndex) {
          stopIndex = controlIndex;
          stopRelease = t + 2 + queue;
        }
        blocked = t < stopRelease;
      } else {
        const world = {
          ...control,
          queue: Math.min(queue, control.green * 0.45),
        };
        blocked = !phase(world, route.hour * 3600 + t + departureShift).green;
      }
      if (blocked && gap < 180)
        target = Math.min(
          target,
          Math.sqrt(2 * BRAKE * Math.max(0, gap - 0.12)),
        );
    }
    const nextV = Math.max(
      0,
      v + Math.max(-BRAKE * STEP, Math.min(ACCEL * STEP, target - v)),
    );
    let ds = (v + nextV) * 0.5 * STEP;
    let newV = nextV;
    // A signal can turn red within this integration step. Crossing is permitted
    // only when green at the interpolated stop-line crossing time.
    if (control && s + ds >= control.s && s <= control.s + 0.1) {
      const crossing = ds > 0 ? (STEP * (control.s - s)) / ds : 0;
      const crossesBlocked =
        control.kind === "signal"
          ? !phase(
              { ...control, queue: Math.min(queue, control.green * 0.45) },
              route.hour * 3600 + t + crossing + departureShift,
            ).green
          : blocked;
      if (crossesBlocked) {
        ds = Math.max(0, control.s - s - 0.001);
        newV = 0;
      } else {
        // Preserve the crossing instant in playback; interpolating across a saved
        // wait and acceleration step can otherwise visually cross just before green.
        if (save)
          samples.push({
            t: t + crossing,
            s: control.s,
            v: v + ((newV - v) * crossing) / STEP,
            waiting: false,
            limit: current.limit,
          });
        controlIndex++;
        stopIndex = -1;
        stopRelease = Infinity;
      }
    }
    const remaining = route.length - s;
    if (ds >= remaining - 0.01) {
      ds = remaining;
      newV = 0;
    }
    if (ds < 0.001 && remaining < 0.25) {
      ds = remaining;
      newV = 0;
    }
    s += ds;
    t += STEP;
    v = newV;
    peak = Math.max(peak, v / MPH);
    const isStopped = v < 0.3;
    if (isStopped) {
      stopped += STEP;
      if (!wasStopped && t > 2 && s < route.length - 1) stops++;
    } else moving += STEP;
    wasStopped = isStopped;
    if (save && (Math.round(t / STEP) % 2 === 0 || s >= route.length - 0.01))
      samples.push({
        t,
        s,
        v,
        waiting: isStopped && s < route.length - 0.3,
        limit: current.limit,
      });
  }
  const movingMph = route.length / (moving || t) / MPH;
  return {
    samples,
    duration: Number(t.toFixed(1)),
    movingSeconds: moving,
    stoppedSeconds: stopped,
    stops,
    peakMph: peak,
    movingMph,
    finished: s >= route.length - 0.02,
  };
}
export function riskIndex(ratio: number) {
  // TØI 1034/2009, Table S1, urban/residential injury crashes and fatal crashes.
  // Applying a population mean-speed relationship to two simulated journeys is
  // an illustrative index, not a validated individual-trip probability model.
  const pct = (p: number) => (Math.pow(Math.max(0.01, ratio), p) - 1) * 100;
  return {
    injury: pct(1.2),
    fatal: pct(2.6),
    injuryRange: [pct(0.7), pct(1.7)] as [number, number],
    fatalRange: [pct(0.3), pct(4.9)] as [number, number],
  };
}
export function compare(route: PreparedRoute, overspeed: number): Comparison {
  // The speed observations already include red lights. Add only the positive
  // residual beyond a signal-only baseline, avoiding treating observed average
  // speed as a free-flow cap and then charging red-light delay a second time.
  const calibration = [0, 30, 60, 90].map(
    (shift) => simulate(route, 0, shift, 0, false).duration,
  );
  const expected = calibration.reduce((a, b) => a + b, 0) / calibration.length;
  const q =
    route.observedSeconds && route.controls.length
      ? Math.max(
          0,
          Math.min(
            12,
            (route.observedSeconds - expected) / route.controls.length,
          ),
        )
      : 0;
  const baseline = simulate(route, 0, 0, q),
    faster = simulate(route, overspeed, 0, q);
  if (!baseline.finished || !faster.finished)
    throw new Error(
      "This route exceeded the model time limit. Try a shorter route.",
    );
  const outcomes = [];
  // Same departure for both cars within each pair. Shift by 10s over a 2-minute
  // window; this is a sensitivity range, never a statistical confidence interval.
  for (let i = 0; i < 12; i++) {
    const a = i === 0 ? baseline : simulate(route, 0, i * 10, q, false),
      b = i === 0 ? faster : simulate(route, overspeed, i * 10, q, false);
    outcomes.push(((a.duration - b.duration) / a.duration) * 100);
  }
  outcomes.sort((a, b) => a - b);
  const movingRatio = faster.movingMph / baseline.movingMph,
    risk = riskIndex(movingRatio);
  return {
    baseline,
    faster,
    timeSaved: baseline.duration - faster.duration,
    timeSavedPct:
      ((baseline.duration - faster.duration) / baseline.duration) * 100,
    tripSpeedGainPct: (baseline.duration / faster.duration - 1) * 100,
    movingGainPct: (movingRatio - 1) * 100,
    injuryRiskPct: risk.injury,
    fatalRiskPct: risk.fatal,
    injuryRiskRange: risk.injuryRange,
    fatalRiskRange: risk.fatalRange,
    sensitivity: {
      min: outcomes[0],
      max: outcomes.at(-1)!,
      median: (outcomes[5] + outcomes[6]) / 2,
      samples: 12,
    },
    queueSeconds: q,
    overspeed,
  };
}
export function sampleAt(run: Run, time: number): Sample {
  if (time >= run.duration)
    return { ...run.samples.at(-1)!, v: 0, waiting: false };
  let lo = 0,
    hi = run.samples.length - 1;
  while (lo < hi) {
    const m = Math.ceil((lo + hi) / 2);
    if (run.samples[m].t <= time) lo = m;
    else hi = m - 1;
  }
  const a = run.samples[lo],
    b = run.samples[Math.min(lo + 1, run.samples.length - 1)],
    f = (time - a.t) / (b.t - a.t || 1);
  return { ...a, t: time, s: a.s + (b.s - a.s) * f, v: a.v + (b.v - a.v) * f };
}
