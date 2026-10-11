import type {
  Control,
  Coord,
  PreparedRoute,
  RoutePoint,
  Sources,
} from "./types";
import {
  SpatialLines,
  angle,
  atDistance,
  bearing,
  distance,
  hash,
  normalize,
  onRoute,
} from "./geometry";
let cachedSources: Sources | undefined,
  limits: SpatialLines,
  observations: SpatialLines;
export function prepareRoute(
  response: any,
  sources: Sources,
  hour: number,
): PreparedRoute {
  if (cachedSources !== sources) {
    limits = new SpatialLines(sources.limits.features);
    observations = new SpatialLines(sources.observed.features);
    cachedSources = sources;
  }
  const raw = response.routes?.[0];
  if (!raw) throw new Error("No route geometry was returned.");
  const points: RoutePoint[] = [];
  const turns: { s: number; cap: number }[] = [];
  let s = 0;
  for (const step of raw.legs.flatMap((l: any) => l.steps)) {
    const coords = step.geometry.coordinates as Coord[];
    if (!coords.length) continue;
    const motorway =
      step.intersections?.some((i: any) => i.classes?.includes("motorway")) ||
      /^(I[- ]|US[- ])/.test(step.ref || "");
    const difference = angle(
      step.maneuver.bearing_before || 0,
      step.maneuver.bearing_after || 0,
    );
    if (
      !["depart", "arrive", "new name", "continue", "notification"].includes(
        step.maneuver.type,
      ) &&
      difference > 32
    )
      turns.push({
        s,
        cap: difference > 130 ? 4.0 : difference > 65 ? 5.5 : 8,
      });
    for (let i = 0; i < coords.length; i++) {
      const a = i ? coords[i - 1] : points.at(-1)?.coord || coords[i],
        b = coords[i];
      const len = distance(a, b);
      const n = Math.max(1, Math.ceil(len / 9));
      if (points.length && len < 0.01) continue;
      for (let j = points.length || len < 0.01 ? 1 : 0; j <= n; j++) {
        const coord: [number, number] = [
          a[0] + ((b[0] - a[0]) * j) / n,
          a[1] + ((b[1] - a[1]) * j) / n,
        ];
        if (points.length) s += distance(points.at(-1)!.coord, coord);
        const heading =
          len > 0.1 ? bearing(a, b) : step.maneuver.bearing_after || 0;
        const hit = limits.nearest(coord, heading, step.name || "", 25);
        const observedHit = observations.nearest(coord, heading, "", 30);
        let observed = observedHit?.feature.properties.speeds?.[hour] ?? null;
        // A directional CMP segment should not supply the opposite carriageway.
        const dir = observedHit?.feature.properties.direction || "";
        const expected = (
          { NB: 0, SB: 180, EB: 90, WB: 270 } as Record<string, number>
        )[dir];
        if (expected !== undefined && angle(heading, expected) > 85)
          observed = null;
        points.push({
          coord,
          s,
          limit: hit?.feature.properties.limit || (motorway ? 55 : 25),
          verified: !!hit,
          road: step.name || "Local street",
          observed: observed > 2 && observed < 80 ? observed : null,
          bearing: heading,
        });
      }
    }
  }
  if (points.length < 2 || s < 50)
    throw new Error("Choose a route at least a block long.");
  // Geometric headings at step boundaries are more useful than the old step's
  // terminal bearing for approaching a signal.
  for (let i = 0; i < points.length - 1; i++)
    points[i].bearing = bearing(points[i].coord, points[i + 1].coord);
  const controls: Control[] = [];
  for (const f of sources.signals.features) {
    const hit = onRoute(f.geometry.coordinates, points);
    if (hit.d > 23 || hit.s < 20 || hit.s > s - 12) continue;
    const p = f.properties;
    let cycle = 90,
      green = 40,
      source: Control["source"] = "assumed",
      note =
        "Assumed 90-second cycle, 40-second approach green, and seeded offset.";
    // Historical cards establish cycle length only. Their movement-specific
    // splits, offset reference and priority logic have not been reconstructed.
    if (p.cnn === "23149000") {
      cycle = hour >= 6.5 && hour < 22 ? 120 : 100;
      green = cycle * 0.45;
      source = "documented-cycle";
      note =
        "2015 19th/Sloat card: documented cycle; green split and phase offset remain assumed.";
    }
    if (p.cnn === "23541000" && hour >= 6.5 && hour < 19) {
      cycle = 120;
      green = 54;
      source = "documented-cycle";
      note =
        "2024 3rd/25th card: documented cycle; priority, preemption and phase offset not reconstructed.";
    }
    // The first version does not turn a FREE/FLASH card into a coordinated
    // schedule. It exposes the assumption explicitly in the route summary.
    const phaseAxis =
      Math.abs(Math.cos((hit.bearing * Math.PI) / 180)) >
      Math.abs(Math.sin((hit.bearing * Math.PI) / 180))
        ? 0
        : 1;
    const system = String(p.system || p.id).trim();
    const groupSeed = hash(system) % cycle;
    const progression =
      (f.geometry.coordinates[1] * 111195 + f.geometry.coordinates[0] * 87860) /
      11.176;
    const offset =
      (groupSeed + progression + (phaseAxis * cycle) / 2 + cycle * 10000) %
      cycle;
    controls.push({
      id: String(p.id),
      kind: "signal",
      s: hit.s - 5,
      coord: atDistance(points, hit.s - 5).coord,
      name: p.name,
      cycle,
      green,
      offset,
      axis: phaseAxis,
      queue: 0,
      source,
      note,
      sourceUrl:
        source === "documented-cycle"
          ? `https://sanfrancisco.nextrequest.com/documents/${p.cnn === "23149000" ? "16282596" : "43475468"}`
          : undefined,
    });
  }
  // Stop signs are matched to the route's street, preventing cross-street stop
  // signs from stopping traffic on the through road. Exact approach placement
  // remains an approximation rather than a lane-level control reconstruction.
  for (const f of sources.stops.features) {
    const p = f.properties;
    if (p.STATUS && !["I", "Implemented", " "].includes(p.STATUS)) continue;
    const hit = onRoute(f.geometry.coordinates, points);
    if (hit.d > 19 || hit.s < 20 || hit.s > s - 12) continue;
    if (controls.some((c) => Math.abs(c.s - hit.s) < 30)) continue;
    const rp = atDistance(points, hit.s),
      road = normalize(points[rp.index].road),
      stopStreet = normalize(p.STREET || p.STREETNAME || "");
    if (!stopStreet || !road.startsWith(stopStreet)) continue;
    controls.push({
      id: "stop-" + p.OBJECTID,
      kind: "stop",
      s: hit.s - 4,
      coord: atDistance(points, hit.s - 4).coord,
      name: p.CONCATENAT || `${p.STREET} & ${p.X_STREET}`,
      cycle: 0,
      green: 0,
      offset: 0,
      axis: 0,
      queue: 0,
      source: "assumed",
      note: "Recorded stop-sign location; approximate approach matching and two-second dwell.",
    });
  }
  controls.sort((a, b) => a.s - b.s);
  const dedup = controls.filter(
    (c, i) => i === 0 || c.s - controls[i - 1].s > 24,
  );
  let verified = 0,
    observedDistance = 0,
    observedSeconds = 0;
  for (let i = 1; i < points.length; i++) {
    const d = points[i].s - points[i - 1].s,
      p = points[i - 1];
    if (p.verified) verified += d;
    if (p.observed) {
      observedDistance += d;
      observedSeconds += d / (p.observed * 0.44704);
    }
  }
  return {
    points,
    coordinates: points.map((p) => p.coord),
    length: s,
    controls: dedup,
    turns,
    verifiedFraction: verified / s,
    observedFraction: observedDistance / s,
    observedSeconds:
      observedDistance / s >= 0.35
        ? (observedSeconds * s) / observedDistance
        : null,
    roadNames: [...new Set(points.map((p) => p.road))],
    hour,
    trafficQueue: 0,
    sourceMonth: sources.observed.period || "",
    snapped: response.waypoints.map((w: any) => w.location),
  };
}
