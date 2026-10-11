export type Coord = [number, number];
export type Feature = {
  type: "Feature";
  geometry: { type: string; coordinates: any };
  properties: Record<string, any>;
};
export type Collection = {
  type: "FeatureCollection";
  features: Feature[];
  period?: string;
};
export type Sources = {
  limits: Collection;
  signals: Collection;
  stops: Collection;
  observed: Collection;
  streets: Collection;
  provenance: Record<string, any>;
};
export type Place = {
  id: string;
  label: string;
  coordinates: Coord;
  neighborhood?: string;
  landmark?: string;
  kind?: "address" | "landmark" | "place";
  address?: string;
  category?: string;
};
export type RoutePoint = {
  coord: Coord;
  s: number;
  limit: number;
  verified: boolean;
  road: string;
  observed: number | null;
  bearing: number;
};
export type Control = {
  id: string;
  kind: "signal" | "stop";
  s: number;
  coord: Coord;
  name: string;
  cycle: number;
  green: number;
  offset: number;
  axis: number;
  queue: number;
  source: "assumed" | "documented-cycle";
  sourceUrl?: string;
  note?: string;
};
export type PreparedRoute = {
  points: RoutePoint[];
  coordinates: Coord[];
  length: number;
  controls: Control[];
  turns: { s: number; cap: number }[];
  verifiedFraction: number;
  observedFraction: number;
  observedSeconds: number | null;
  roadNames: string[];
  hour: number;
  trafficQueue: number;
  sourceMonth: string;
  snapped: Coord[];
};
export type Sample = {
  t: number;
  s: number;
  v: number;
  waiting: boolean;
  limit: number;
};
export type Run = {
  samples: Sample[];
  duration: number;
  movingSeconds: number;
  stoppedSeconds: number;
  stops: number;
  peakMph: number;
  movingMph: number;
  finished: boolean;
};
export type Comparison = {
  baseline: Run;
  faster: Run;
  timeSaved: number;
  timeSavedPct: number;
  tripSpeedGainPct: number;
  movingGainPct: number;
  injuryRiskPct: number;
  fatalRiskPct: number;
  injuryRiskRange: [number, number];
  fatalRiskRange: [number, number];
  sensitivity: { min: number; max: number; median: number; samples: number };
  queueSeconds: number;
  overspeed: number;
};
