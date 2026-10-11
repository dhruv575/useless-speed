import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  LoaderCircle,
  Moon,
  Pause,
  Play,
  Sun,
  Sunrise,
  Sunset,
  X,
} from "lucide-react";
import CityMap from "./CityMap";
import AddressInput from "./AddressInput";
import type {
  Comparison,
  Coord,
  Place,
  PreparedRoute,
  Sources,
} from "./model/types";
import { liveComparison } from "./model/live";
import { themeForHour } from "./theme";

const periods = [
  { hour: 8, label: "Morning", time: "8 AM", Icon: Sunrise },
  { hour: 12, label: "Midday", time: "12 PM", Icon: Sun },
  { hour: 17, label: "Evening", time: "5 PM", Icon: Sunset },
  { hour: 22, label: "Night", time: "10 PM", Icon: Moon },
];
const metrics = [
  {
    key: "movingGainPct",
    label: "Car 2 actual average moving-speed increase (%)",
    detail:
      "Car 2's average moving speed compared with Car 1's, over the route portion both have driven. Excludes standing still. Acceleration, braking and turns can make this lower than the target. Signal timings are mostly assumed.",
  },
  {
    key: "timeSavedPct",
    label: "How much time did car 2 save (%)",
    detail:
      "Time saved over the portion of the route both cars have driven. Finalizes when both arrive. This is an exploratory model with mostly assumed signal phases.",
  },
  {
    key: "injuryRiskPct",
    label: "How much likelier was car 2 to be involved in a crash (%)",
    detail:
      "Illustrative relative injury-crash risk index from population speed–risk research. Excludes property-damage-only crashes. Not a measured personal or trip crash probability.",
  },
  {
    key: "fatalRiskPct",
    label: "How much likelier was car 2 to be involved in a fatal crash (%)",
    detail:
      "Illustrative relative fatal-crash risk index from population speed–risk research. Not a measured personal or trip probability, or specifically the driver's risk of death.",
  },
] as const;

async function json(url: string, signal?: AbortSignal) {
  const response = await fetch(url, { signal });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Could not load city data.");
  return data;
}

export default function App() {
  const [sources, setSources] = useState<Sources | null>(null);
  const [start, setStart] = useState<Place | null>(null);
  const [end, setEnd] = useState<Place | null>(null);
  const [hour, setHour] = useState(8);
  const [overspeed, setOverspeed] = useState(20);
  const [pinMode, setPinMode] = useState<"start" | "end" | null>(null);
  const [route, setRoute] = useState<PreparedRoute | null>(null);
  const [result, setResult] = useState<Comparison | null>(null);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const worker = useRef<Worker | null>(null);
  const requestId = useRef(0);
  const cachedRoute = useRef<{ key: string; raw: unknown } | null>(null);
  const timeRef = useRef(0);
  const theme = themeForHour(hour);

  useLayoutEffect(() => {
    const freeze = document.createElement("style");
    freeze.textContent = "*,*::before,*::after{transition:none!important}";
    document.head.append(freeze);
    document.documentElement.dataset.theme = theme;
    void document.body.offsetHeight;
    let secondFrame = 0;
    const firstFrame = requestAnimationFrame(() => {
      secondFrame = requestAnimationFrame(() => freeze.remove());
    });
    return () => {
      cancelAnimationFrame(firstFrame);
      cancelAnimationFrame(secondFrame);
      freeze.remove();
    };
  }, [theme]);

  useEffect(() => {
    const controller = new AbortController();
    const w = new Worker(new URL("./model/worker.ts", import.meta.url), {
      type: "module",
    });
    worker.current = w;
    w.onmessage = ({ data }) => {
      if (data.type === "ready") {
        setBusy(false);
        return;
      }
      if (data.id !== requestId.current) return;
      if (data.type === "result") {
        setRoute(data.route);
        setResult(data.comparison);
        timeRef.current = 0;
        setTime(0);
        setBusy(false);
        setPlaying(true);
      }
      if (data.type === "error") {
        setError(data.error);
        setBusy(false);
      }
    };
    w.onerror = () => {
      setError("The simulation stopped. Reload to try again.");
      setBusy(false);
    };
    (async () => {
      try {
        const [limits, signals, stops, observed, streets, provenance] =
          await Promise.all(
            [
              "speed-limits",
              "signals",
              "stop-signs",
              "observed-speeds",
              "streets",
              "provenance",
            ].map((name) => json(`/data/${name}.json`, controller.signal)),
          );
        const data = { limits, signals, stops, observed, streets, provenance };
        setSources(data);
        w.postMessage({ type: "init", sources: data });
      } catch (e) {
        if (!controller.signal.aborted) {
          setError(
            e instanceof Error ? e.message : "Could not load city data.",
          );
          setBusy(false);
        }
      }
    })();
    return () => {
      controller.abort();
      w.terminate();
    };
  }, []);

  useEffect(() => {
    const escape = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPinMode(null);
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, []);

  const duration = result
    ? Math.max(result.baseline.duration, result.faster.duration)
    : 0;
  const evaluate = useMemo(
    () => (result ? liveComparison(result) : null),
    [result],
  );
  const values = evaluate && time > 0 ? evaluate(time) : null;
  const finished = duration > 0 && time >= duration;
  const progress = duration ? time / duration : 0;

  useEffect(() => {
    if (!playing) return;
    let frame = 0,
      previous = performance.now();
    const advance = (now: number) => {
      timeRef.current = Math.min(
        duration,
        timeRef.current + Math.max(0, now - previous) * 0.06,
      );
      previous = now;
      setTime(timeRef.current);
      if (timeRef.current >= duration) {
        setPlaying(false);
        return;
      }
      frame = requestAnimationFrame(advance);
    };
    frame = requestAnimationFrame(advance);
    return () => cancelAnimationFrame(frame);
  }, [playing, duration]);

  function invalidate(clearRoute = false) {
    setPlaying(false);
    setResult(null);
    setTime(0);
    timeRef.current = 0;
    setError("");
    if (clearRoute) setRoute(null);
  }
  function changePlace(which: "start" | "end", place: Place | null) {
    invalidate(true);
    if (which === "start") setStart(place);
    else setEnd(place);
    setPinMode(null);
  }
  function pin(coord: Coord, which: "start" | "end") {
    if (busy) return;
    if (
      coord[0] < -122.525 ||
      coord[0] > -122.345 ||
      coord[1] < 37.706 ||
      coord[1] > 37.835
    ) {
      setError("Choose a point within San Francisco.");
      return;
    }
    changePlace(which, {
      id: coord.join(","),
      label: `${coord[1].toFixed(4)}, ${coord[0].toFixed(4)}`,
      coordinates: coord,
    });
  }
  async function simulate() {
    if (playing) {
      setPlaying(false);
      return;
    }
    if (result && !finished) {
      setPlaying(true);
      return;
    }
    if (!sources || !worker.current || !start || !end) return;
    if (result && finished) {
      timeRef.current = 0;
      setTime(0);
      setPlaying(true);
      return;
    }
    setBusy(true);
    setPinMode(null);
    setError("");
    const id = ++requestId.current;
    try {
      const key = [start.coordinates, end.coordinates].join("|");
      const raw =
        cachedRoute.current?.key === key
          ? cachedRoute.current.raw
          : await json(
              `/api/route?start=${start.coordinates.join(",")}&end=${end.coordinates.join(",")}`,
            );
      if (id !== requestId.current) return;
      cachedRoute.current = { key, raw };
      worker.current.postMessage({
        type: "calculate",
        id,
        raw,
        hour,
        overspeed,
      });
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Could not calculate this route.",
      );
      setBusy(false);
    }
  }

  return (
    <div className="app" autoCapitalize="none">
      <main className="main">
        <CityMap
          theme={theme}
          sources={sources}
          route={route}
          result={result}
          time={time}
          start={start}
          end={end}
          pinMode={pinMode}
          onPin={pin}
          disabled={busy}
        />
      </main>
      <aside className="sidebar" aria-label="Simulation configuration">
        <fieldset className="configuration" disabled={busy}>
          <div className="addresses">
            <AddressInput
              label="Starting point"
              letter="A"
              place={start}
              onChange={(p) => changePlace("start", p)}
              onPin={() => setPinMode(pinMode === "start" ? null : "start")}
              pinning={pinMode === "start"}
            />
            <AddressInput
              label="Destination"
              letter="B"
              place={end}
              onChange={(p) => changePlace("end", p)}
              onPin={() => setPinMode(pinMode === "end" ? null : "end")}
              pinning={pinMode === "end"}
            />
          </div>
          <fieldset className="time-setting">
            <legend>Time of day</legend>
            <div className="time-toggle">
              {periods.map(({ hour: h, label, time: clock, Icon }) => (
                <label
                  className="time-option"
                  key={h}
                  title={`${label} · ${clock}`}
                >
                  <input
                    type="radio"
                    name="time-of-day"
                    aria-label={`${label} · ${clock}`}
                    checked={hour === h}
                    onChange={() => {
                      setHour(h);
                      invalidate();
                    }}
                  />
                  <span>
                    <Icon size={21} />
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
          <div className="speed-setting">
            <div className="slider-heading">
              <label htmlFor="overspeed">
                Car 2 target cruising speed above the limit (%)
              </label>
              <output htmlFor="overspeed">
                {overspeed}
                <span>%</span>
              </output>
            </div>
            <input
              id="overspeed"
              type="range"
              min="0"
              max="100"
              step="5"
              value={overspeed}
              style={{
                background: `linear-gradient(to right, var(--ink) ${overspeed}%, var(--track) ${overspeed}%)`,
              }}
              onChange={(e) => {
                setOverspeed(+e.target.value);
                invalidate();
              }}
            />
          </div>
        </fieldset>
        <button
          className="simulate-button"
          onClick={simulate}
          disabled={busy || !start || !end || !sources}
          aria-busy={busy}
          aria-label={
            playing
              ? "Pause simulation"
              : result && !finished
                ? "Resume simulation"
                : "Simulate"
          }
        >
          <span
            className="button-progress"
            style={{ width: `${progress * 100}%` }}
          />
          <span>
            {playing ? "Pause" : result && !finished ? "Resume" : "Simulate"}
          </span>
          {busy ? (
            <LoaderCircle size={16} className="spinner" />
          ) : playing ? (
            <Pause size={15} />
          ) : (
            <Play size={14} fill="currentColor" />
          )}
        </button>
        {error && (
          <div className="error-message" role="alert">
            <span>{error}</span>
            <button aria-label="Dismiss error" onClick={() => setError("")}>
              <X size={15} />
            </button>
          </div>
        )}
        <div className="trip-times" aria-label="Elapsed trip times">
          {[
            { label: "Time car 1", run: result?.baseline },
            { label: "Time car 2", run: result?.faster },
          ].map(({ label, run }) => {
            const minutes = run
              ? Math.round(Math.min(time, run.duration) / 60)
              : null;
            return (
              <div className="trip-time" key={label}>
                <span className="metric-label">{label}</span>
                <output
                  className={minutes === null ? "empty" : ""}
                  aria-label={label}
                >
                  {minutes === null ? (
                    "—"
                  ) : (
                    <>
                      {minutes}
                      <small>min</small>
                    </>
                  )}
                </output>
              </div>
            );
          })}
        </div>
        <div
          className="metrics"
          aria-label="Live simulation results"
          data-state={
            finished
              ? "finished"
              : playing
                ? "running"
                : result
                  ? "paused"
                  : "empty"
          }
        >
          {metrics.map(({ key, label, detail }, i) => {
            const value = values?.[key];
            return (
              <div
                className={`metric metric-${i + 1}`}
                key={key}
                tabIndex={0}
                aria-describedby={`metric-detail-${i}`}
              >
                <span className="metric-label">{label}</span>
                <output
                  className={value === undefined ? "empty" : ""}
                  aria-label={label}
                >
                  {value === undefined ? (
                    "—"
                  ) : (
                    <>
                      {Math.abs(value) < 0.05 ? "0.0" : value.toFixed(1)}
                      <small>%</small>
                    </>
                  )}
                </output>
                <span
                  id={`metric-detail-${i}`}
                  role="tooltip"
                  className="metric-tooltip"
                >
                  {detail}
                </span>
              </div>
            );
          })}
        </div>
      </aside>
    </div>
  );
}
