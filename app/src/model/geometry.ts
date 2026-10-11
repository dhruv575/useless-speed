import type { Coord, Feature, RoutePoint } from "./types";
const LAT = 111195,
  LON = 87860;
export const distance = (a: Coord, b: Coord) =>
  Math.hypot((b[0] - a[0]) * LON, (b[1] - a[1]) * LAT);
export const bearing = (a: Coord, b: Coord) =>
  ((Math.atan2((b[0] - a[0]) * LON, (b[1] - a[1]) * LAT) * 180) / Math.PI +
    360) %
  360;
export const angle = (a: number, b: number) =>
  Math.abs(((a - b + 540) % 360) - 180);
export const axisAngle = (a: number, b: number) =>
  Math.min(angle(a, b), angle(a, (b + 180) % 360));
export function project(p: Coord, a: Coord, b: Coord) {
  const dx = (b[0] - a[0]) * LON,
    dy = (b[1] - a[1]) * LAT,
    px = (p[0] - a[0]) * LON,
    py = (p[1] - a[1]) * LAT;
  const t = Math.max(
    0,
    Math.min(1, (px * dx + py * dy) / (dx * dx + dy * dy || 1)),
  );
  return {
    t,
    d: Math.hypot(px - dx * t, py - dy * t),
    coord: [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t] as Coord,
  };
}
export function onRoute(p: Coord, points: RoutePoint[]) {
  let best = { d: Infinity, s: 0, coord: p, bearing: 0 };
  for (let i = 1; i < points.length; i++) {
    const hit = project(p, points[i - 1].coord, points[i].coord);
    if (hit.d < best.d)
      best = {
        d: hit.d,
        s: points[i - 1].s + (points[i].s - points[i - 1].s) * hit.t,
        coord: hit.coord,
        bearing: points[i - 1].bearing,
      };
  }
  return best;
}
export function atDistance(points: RoutePoint[], s: number) {
  let lo = 0,
    hi = points.length - 1;
  while (lo < hi) {
    const mid = Math.ceil((lo + hi) / 2);
    if (points[mid].s <= s) lo = mid;
    else hi = mid - 1;
  }
  const a = points[lo],
    b = points[Math.min(lo + 1, points.length - 1)],
    t = b.s > a.s ? Math.max(0, Math.min(1, (s - a.s) / (b.s - a.s))) : 0;
  return {
    coord: [
      a.coord[0] + (b.coord[0] - a.coord[0]) * t,
      a.coord[1] + (b.coord[1] - a.coord[1]) * t,
    ] as Coord,
    bearing: a.bearing,
    limit: a.limit,
    index: lo,
  };
}
export const hash = (s: string) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++)
    h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
};
export const normalize = (s: string) =>
  s
    .toUpperCase()
    .replace(/\bSTREET\b/g, "ST")
    .replace(/\bAVENUE\b/g, "AVE")
    .replace(/\bBOULEVARD\b/g, "BLVD")
    .replace(/\b0+(\d)/g, "$1")
    .replace(/[^A-Z0-9]/g, "");
type Segment = { a: Coord; b: Coord; feature: Feature; heading: number };
export class SpatialLines {
  grid = new Map<string, Segment[]>();
  constructor(features: Feature[]) {
    for (const feature of features) {
      const lines =
        feature.geometry.type === "MultiLineString"
          ? feature.geometry.coordinates
          : [feature.geometry.coordinates];
      for (const line of lines) {
        for (let i = 1; i < line.length; i++) {
          const a = line[i - 1] as Coord,
            b = line[i] as Coord;
          const seg = { a, b, feature, heading: bearing(a, b) };
          for (
            let x = Math.floor(Math.min(a[0], b[0]) * 500);
            x <= Math.floor(Math.max(a[0], b[0]) * 500);
            x++
          )
            for (
              let y = Math.floor(Math.min(a[1], b[1]) * 500);
              y <= Math.floor(Math.max(a[1], b[1]) * 500);
              y++
            ) {
              const key = x + "," + y;
              const arr = this.grid.get(key) || [];
              arr.push(seg);
              this.grid.set(key, arr);
            }
        }
      }
    }
  }
  nearest(p: Coord, heading: number, name = "", max = 28) {
    let best: { feature: Feature; distance: number; score: number } | null =
      null;
    const x = Math.floor(p[0] * 500),
      y = Math.floor(p[1] * 500);
    for (let dx = -1; dx <= 1; dx++)
      for (let dy = -1; dy <= 1; dy++)
        for (const seg of this.grid.get(x + dx + "," + (y + dy)) || []) {
          const a = axisAngle(heading, seg.heading);
          if (a > 35) continue;
          const d = project(p, seg.a, seg.b).d;
          if (d > max) continue;
          const namePenalty =
            name &&
            normalize(name) !== normalize(seg.feature.properties.name || "")
              ? 8
              : 0;
          const score = d + a * 0.15 + namePenalty;
          if (!best || score < best.score)
            best = { feature: seg.feature, distance: d, score };
        }
    return best;
  }
}
