import { useEffect, useRef, useState } from "react";
import {
  Map as LibreMap,
  Marker,
  NavigationControl,
  LngLatBounds,
  setWorkerUrl,
} from "maplibre-gl";
import mapWorkerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import type { GeoJSONSource, StyleSpecification } from "maplibre-gl";
import mapStyle from "./map-style.json";
import { LocateFixed } from "lucide-react";
import type {
  Coord,
  Place,
  PreparedRoute,
  Comparison,
  Sources,
} from "./model/types";
import { atDistance } from "./model/geometry";
import { phase, sampleAt, MPH } from "./model/simulation";
const empty = { type: "FeatureCollection", features: [] } as const;
setWorkerUrl(mapWorkerUrl);
export default function CityMap({
  sources,
  route,
  result,
  time,
  start,
  end,
  pinMode,
  onPin,
  disabled,
}: {
  sources: Sources | null;
  route: PreparedRoute | null;
  result: Comparison | null;
  time: number;
  start: Place | null;
  end: Place | null;
  pinMode: "start" | "end" | null;
  onPin: (coord: Coord, which: "start" | "end") => void;
  disabled: boolean;
}) {
  const container = useRef<HTMLDivElement>(null),
    map = useRef<LibreMap | null>(null),
    [ready, setReady] = useState(false),
    [tileError, setTileError] = useState(false),
    [mapError, setMapError] = useState("");
  const endpointMarkers = useRef<Marker[]>([]),
    cars = useRef<Marker[]>([]),
    selection = useRef({ pinMode, onPin });
  selection.current = { pinMode, onPin };
  useEffect(() => {
    if (!container.current) return;
    let m: LibreMap;
    try {
      m = new LibreMap({
        container: container.current,
        center: [-122.439, 37.767],
        zoom: 12.7,
        pitch: 0,
        bearing: 0,
        dragRotate: false,
        pitchWithRotate: false,
        touchPitch: false,
        maxPitch: 0,
        minZoom: 10,
        maxZoom: 19,
        attributionControl: { compact: false },
        style: mapStyle as unknown as StyleSpecification,
      });
    } catch (e) {
      setMapError(
        "The interactive map requires WebGL. Enable hardware acceleration and reload.",
      );
      return;
    }
    map.current = m;
    m.touchZoomRotate.disableRotation();
    m.addControl(new NavigationControl({ showCompass: false }), "bottom-right");
    m.on("click", (e) => {
      const p = selection.current;
      if (p.pinMode) p.onPin([e.lngLat.lng, e.lngLat.lat], p.pinMode);
    });
    m.on("error", (e) => {
      if ((e as any).sourceId === "openmaptiles") {
        setTileError(true);
        if (m.getLayer("street-fallback"))
          m.setLayoutProperty("street-fallback", "visibility", "visible");
      }
    });
    m.on("load", () => {
      m.addSource("route", { type: "geojson", data: empty as any });
      m.addLayer({
        id: "route-halo",
        type: "line",
        source: "route",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": "#ffffff",
          "line-width": 10,
          "line-opacity": 0.95,
        },
      });
      m.addLayer({
        id: "route-line",
        type: "line",
        source: "route",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#397785", "line-width": 5 },
      });
      m.addSource("controls", { type: "geojson", data: empty as any });
      m.addLayer({
        id: "control-points",
        type: "circle",
        source: "controls",
        paint: {
          "circle-radius": ["case", ["==", ["get", "kind"], "stop"], 3, 5],
          "circle-color": ["get", "color"],
          "circle-stroke-color": "#fff",
          "circle-stroke-width": 2,
        },
      });
      for (let i = 0; i < 2; i++) {
        const el = document.createElement("div");
        el.className = "map-endpoint " + (i ? "end" : "start");
        el.textContent = i ? "B" : "A";
        el.setAttribute(
          "aria-label",
          (i ? "Destination" : "Starting point") + " pin",
        );
        const marker = new Marker({
          element: el,
          draggable: true,
          offset: [0, -22],
        })
          .setLngLat([-122.44, 37.76])
          .addTo(m);
        marker.on("dragend", () => {
          const p = marker.getLngLat();
          selection.current.onPin([p.lng, p.lat], i ? "end" : "start");
        });
        endpointMarkers.current.push(marker);
        const vehicle = document.createElement("div");
        vehicle.className = "car-marker " + (i ? "faster" : "baseline");
        const body = document.createElement("div");
        body.className = "car-body";
        body.textContent = i ? "2" : "1";
        vehicle.appendChild(body);
        cars.current.push(
          new Marker({ element: vehicle, rotationAlignment: "map" })
            .setLngLat([-122.44, 37.76])
            .addTo(m),
        );
      }
      setReady(true);
    });
    return () => {
      m.remove();
      map.current = null;
      endpointMarkers.current = [];
      cars.current = [];
      setReady(false);
    };
  }, []);
  useEffect(() => {
    if (!ready || !map.current) return;
    map.current.getCanvas().style.cursor = pinMode ? "crosshair" : "";
    endpointMarkers.current.forEach((m) => m.setDraggable(!disabled));
  }, [pinMode, ready, disabled]);
  useEffect(() => {
    if (ready && sources)
      (map.current?.getSource("streets") as GeoJSONSource)?.setData(
        sources.streets as any,
      );
  }, [ready, sources]);
  useEffect(() => {
    if (!ready) return;
    [start, end].forEach((p, i) => {
      const marker = endpointMarkers.current[i];
      if (marker) {
        marker.getElement().style.display = p ? "" : "none";
        if (p) marker.setLngLat(p.coordinates);
      }
    });
  }, [ready, start, end]);
  function fit() {
    if (!map.current || (!route && (!start || !end))) return;
    const bounds = new LngLatBounds();
    (route?.coordinates || [start!.coordinates, end!.coordinates]).forEach(
      (c) => bounds.extend(c),
    );
    const compact = window.innerWidth <= 700;
    map.current.fitBounds(bounds, {
      padding: {
        top: compact ? 50 : 90,
        right: compact ? 55 : 110,
        bottom: compact ? 55 : 90,
        left: compact ? 35 : window.innerWidth <= 1050 ? 370 : 410,
      },
      maxZoom: 15.7,
      duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? 0
        : 500,
    });
  }
  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    const resize = () => fit();
    m.on("resize", resize);
    return () => {
      m.off("resize", resize);
    };
  }, [ready, route, start, end]);
  useEffect(() => {
    if (!ready || !map.current) return;
    (map.current.getSource("route") as GeoJSONSource).setData(
      route
        ? {
            type: "Feature",
            geometry: { type: "LineString", coordinates: route.coordinates },
            properties: {},
          }
        : (empty as any),
    );
    if (route || (start && end)) fit();
  }, [ready, route, start, end]);
  useEffect(() => {
    if (!ready || !map.current) return;
    (map.current.getSource("controls") as GeoJSONSource).setData({
      type: "FeatureCollection",
      features: (route?.controls || []).map((c) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: c.coord },
        properties: {
          kind: c.kind,
          color:
            c.kind === "stop"
              ? "#a18465"
              : phase(
                    { ...c, queue: result?.queueSeconds || 0 },
                    route!.hour * 3600 + time,
                  ).green
                ? "#3e9276"
                : "#b85a51",
        },
      })),
    });
    cars.current.forEach((marker, i) => {
      marker.getElement().style.display = result && route ? "" : "none";
      if (!result || !route) return;
      const run = i ? result.faster : result.baseline,
        sample = sampleAt(run, time),
        p = atDistance(route.points, sample.s);
      marker.setLngLat(p.coord).setRotation(p.bearing);
      marker.getElement().title = `${i ? "Car 2" : "Car 1"} · ${time >= run.duration ? "Arrived" : sample.waiting ? "Stopped" : Math.round(sample.v / MPH) + " mph"}`;
    });
  }, [ready, route, result, time]);
  return (
    <div className={"city-map " + (pinMode ? "pinning" : "")}>
      <div
        ref={container}
        className="map-canvas"
        aria-label="Top-down map of San Francisco"
      />
      <button
        className="fit-button icon-button"
        aria-label="Fit route on map"
        title="Fit route"
        onClick={fit}
        disabled={!route && (!start || !end)}
      >
        <LocateFixed size={19} />
      </button>
      {(tileError || mapError) && (
        <div className="map-notice" role="status">
          {mapError ||
            "Map tiles unavailable. Showing the local street network."}
        </div>
      )}
    </div>
  );
}
