import type { StyleSpecification } from "maplibre-gl";
import baseStyle from "./map-style.json";

export type Theme = "morning" | "midday" | "evening" | "night";

export function themeForHour(hour: number): Theme {
  if (hour >= 20 || hour < 6) return "night";
  if (hour >= 16) return "evening";
  return hour >= 11 ? "midday" : "morning";
}

export const mapPalettes = {
  morning: {
    land: "#f3f0e7",
    residential: "#eeeade",
    park: "#e1e6d6",
    wood: "#dbe3cf",
    water: "#d5e2e1",
    building: "#e6e2d7",
    outline: "#ddd9ce",
    road: "#fffdf7",
    casing: "#dcd8cd",
    path: "#e1ddcf",
    label: "#73786a",
    route: "#397785",
    halo: "#fffdf7",
  },
  midday: {
    land: "#f1f4f2",
    residential: "#e9efeb",
    park: "#dce8db",
    wood: "#d5e3d4",
    water: "#cedfe6",
    building: "#e1e8e4",
    outline: "#d7dfdb",
    road: "#ffffff",
    casing: "#d8e0db",
    path: "#dee5df",
    label: "#64776e",
    route: "#347c91",
    halo: "#ffffff",
  },
  evening: {
    land: "#eee3de",
    residential: "#e8dcd6",
    park: "#dcded0",
    wood: "#d2d7c6",
    water: "#c9d3da",
    building: "#e0d1cb",
    outline: "#d6c5bf",
    road: "#fbf2e8",
    casing: "#d7c7bf",
    path: "#dcd1c5",
    label: "#796d70",
    route: "#8b6176",
    halo: "#fbf2e8",
  },
  night: {
    land: "#1b2330",
    residential: "#202936",
    park: "#263a37",
    wood: "#213431",
    water: "#101c2a",
    building: "#273241",
    outline: "#303d4d",
    road: "#45546a",
    casing: "#18212d",
    path: "#35473f",
    label: "#a7b5c6",
    route: "#91c5d0",
    halo: "#16202c",
  },
} satisfies Record<Theme, Record<string, string>>;

// Change paint only: routes, pins, camera and the fallback stay mounted.
export function themedMapStyle(theme: Theme): StyleSpecification {
  const style = structuredClone(baseStyle) as unknown as StyleSpecification;
  const p = mapPalettes[theme];
  style.transition = { duration: 0, delay: 0 };
  for (const layer of style.layers) {
    const paint = layer.paint as Record<string, unknown> | undefined;
    if (!paint) continue;
    for (const property of Object.keys(paint)) {
      if (!property.endsWith("-color")) continue;
      const id = layer.id;
      paint[property] =
        property === "text-color"
          ? p.label
          : property === "text-halo-color"
            ? p.land
            : property === "fill-outline-color"
              ? p.outline
              : id === "background"
                ? p.land
                : id === "park"
                  ? p.park
                  : id.includes("wood")
                    ? p.wood
                    : id.startsWith("water")
                      ? p.water
                      : id === "building"
                        ? p.building
                        : id.includes("residential")
                          ? p.residential
                          : id.includes("casing")
                            ? p.casing
                            : id.includes("path")
                              ? p.path
                              : p.road;
    }
  }
  return style;
}
