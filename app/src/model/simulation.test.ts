import test from "node:test";
import assert from "node:assert/strict";
import {
  compare,
  simulate,
  phase,
  riskIndex,
  sampleAt,
  MPH,
} from "./simulation";
import type { PreparedRoute, Control } from "./types";
import { liveComparison } from "./live";

function route(controls: Control[] = []): PreparedRoute {
  return {
    points: Array.from({ length: 201 }, (_, i) => ({
      coord: [-122.44, 37.75 + (i * 10) / 111195],
      s: i * 10,
      limit: 25,
      verified: true,
      road: "Test street",
      observed: null,
      bearing: 0,
    })),
    coordinates: [],
    length: 2000,
    controls,
    turns: [],
    verifiedFraction: 1,
    observedFraction: 0,
    observedSeconds: null,
    roadNames: ["Test street"],
    hour: 8,
    trafficQueue: 0,
    sourceMonth: "",
    snapped: [],
  };
}
const signal: Control = {
  id: "1",
  kind: "signal",
  s: 250,
  coord: [-122.44, 37.752],
  name: "Test",
  cycle: 90,
  green: 40,
  offset: 0,
  axis: 0,
  queue: 0,
  source: "assumed",
};
test("zero excess speed gives identical trajectories, arrival times and risk indices", () => {
  const result = compare(route([signal]), 0);
  assert.deepEqual(result.baseline, result.faster);
  assert.equal(result.timeSavedPct, 0);
  assert.equal(result.fatalRiskPct, 0);
  assert.equal(result.sensitivity.max, 0);
});
test("free-flow run respects cruising cap and physically plausible acceleration time", () => {
  const a = simulate(route(), 0),
    b = simulate(route(), 100);
  assert.ok(a.finished && b.finished);
  assert.ok(a.peakMph <= 25.0001);
  assert.ok(b.peakMph <= 50.0001);
  assert.ok(a.duration > 2000 / (25 * MPH));
  assert.ok(a.duration < 2000 / (25 * MPH) + 15);
  assert.ok(b.duration < a.duration * 0.65);
  assert.ok(b.duration > a.duration * 0.5);
});
test("a vehicle never passes the stop line on red, across many departure phases", () => {
  for (let shift = 0; shift < 90; shift += 3) {
    const r = route([signal]),
      run = simulate(r, 100, shift);
    assert.ok(run.finished);
    const i = run.samples.findIndex((p) => p.s > signal.s),
      a = run.samples[i - 1],
      b = run.samples[i];
    const crossing = a.t + ((b.t - a.t) * (signal.s - a.s)) / (b.s - a.s);
    assert.ok(
      phase(signal, 8 * 3600 + crossing + shift).green,
      `crossed red at departure shift ${shift}`,
    );
  }
});
test("stop signs force a dwell and contribute delay for both cars", () => {
  const stop = { ...signal, kind: "stop" as const },
    r = route([stop]);
  for (const speed of [0, 100]) {
    const run = simulate(r, speed);
    assert.ok(run.finished);
    assert.ok(run.stoppedSeconds >= 1.8);
    assert.ok(run.duration > simulate(route(), speed).duration);
  }
});
test("runs are deterministic, sample playback is bounded, and time accounting balances", () => {
  const r = route([signal]),
    a = simulate(r, 30);
  assert.deepEqual(a, simulate(r, 30));
  assert.ok(Math.abs(a.duration - a.movingSeconds - a.stoppedSeconds) < 1e-6);
  assert.equal(sampleAt(a, a.duration + 100).v, 0);
  assert.equal(sampleAt(a, 0).s, 0);
  assert.ok(sampleAt(a, a.duration / 2).s > 0);
  assert.ok(sampleAt(a, a.duration / 2).s < r.length);
});
test("risk indices use urban exponents and reject invalid speed settings", () => {
  assert.ok(Math.abs(riskIndex(1.2).fatal - (1.2 ** 2.6 - 1) * 100) < 1e-9);
  assert.throws(() => simulate(route(), 101));
  assert.throws(() => simulate(route(), -1));
});

test("live results do not reveal an unearned speed advantage before either car reaches the limit", () => {
  const result = compare(route([signal]), 20);
  assert.ok(result.movingGainPct > 0);
  const live = liveComparison(result)(3);
  assert.equal(live.movingGainPct, 0);
  assert.equal(live.timeSavedPct, 0);
  assert.equal(live.injuryRiskPct, 0);
  assert.equal(live.fatalRiskPct, 0);
});

test("live comparisons stay equal for identical cars through red-light waits and finalize exactly", () => {
  const result = compare(route([signal]), 0),
    read = liveComparison(result);
  for (let time = 1; time < result.baseline.duration; time += 2) {
    assert.equal(read(time).timeSavedPct, 0);
    assert.equal(read(time).movingGainPct, 0);
  }
  const different = compare(route([signal]), 20);
  assert.deepEqual(
    liveComparison(different)(
      Math.max(different.baseline.duration, different.faster.duration),
    ),
    different,
  );
});
