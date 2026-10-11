import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createSearch, inCity as bounds } from "./server/search.mjs";
const root = path.dirname(fileURLToPath(import.meta.url));
const cacheDir = process.env.CACHE_DIR || path.join(root, "cache");
fs.mkdirSync(cacheDir, { recursive: true });
const { search, addressCount, placeCount } = createSearch(
  JSON.parse(fs.readFileSync(path.join(root, "data", "addresses.json"), "utf8")),
  JSON.parse(fs.readFileSync(path.join(root, "data", "places.json"), "utf8")),
);
let nextRouteTime = 0;
const inFlight = new Map();
const json = (res, status, data) => {
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  res.end(JSON.stringify(data));
};
async function route(start, end) {
  const key = [...start, ...end].map((n) => n.toFixed(5)).join("_"),
    cache = path.join(cacheDir, key + ".json");
  if (fs.existsSync(cache)) return JSON.parse(fs.readFileSync(cache, "utf8"));
  if (inFlight.has(key)) return inFlight.get(key);
  const work = (async () => {
    const now = Date.now(),
      slot = Math.max(now, nextRouteTime);
    nextRouteTime = slot + 1100;
    await new Promise((r) => setTimeout(r, slot - now));
    const base = process.env.ROUTER_URL || "https://router.project-osrm.org";
    const url = `${base}/route/v1/driving/${start.join(",")};${end.join(",")}?overview=full&geometries=geojson&steps=true&annotations=distance,duration`;
    const response = await fetch(url, {
      headers: {
        "User-Agent":
          "UselessSpeedResearch/0.1 (local non-commercial simulation)",
      },
      signal: AbortSignal.timeout(25000),
    });
    const data = await response.json();
    if (!response.ok || data.code !== "Ok")
      throw new Error(
        data.message ||
          "No driving route found. Try moving a pin onto a nearby street.",
      );
    if (data.routes[0].distance > 35000)
      throw new Error(
        "That route leaves the street-scale model. Choose two points on the San Francisco peninsula.",
      );
    fs.writeFileSync(cache, JSON.stringify(data));
    return data;
  })();
  inFlight.set(key, work);
  try {
    return await work;
  } finally {
    inFlight.delete(key);
  }
}
const server = http.createServer(async (req, res) => {
  try {
    const u = new URL(req.url, "http://localhost");
    if (u.pathname === "/api/health")
      return json(res, 200, { ok: true, addresses: addressCount, places: placeCount });
    if (u.pathname === "/api/search") {
      return json(res, 200, search(u.searchParams.get("q") || ""));
    }
    if (u.pathname === "/api/demo")
      return json(
        res,
        200,
        JSON.parse(
          fs.readFileSync(path.join(root, "data", "demo-route.json"), "utf8"),
        ),
      );
    if (u.pathname === "/api/route") {
      const start = (u.searchParams.get("start") || "").split(",").map(Number),
        end = (u.searchParams.get("end") || "").split(",").map(Number);
      if (
        start.length !== 2 ||
        end.length !== 2 ||
        !bounds(start) ||
        !bounds(end)
      )
        return json(res, 400, {
          error: "Choose two locations in San Francisco.",
        });
      if (Math.hypot(start[0] - end[0], start[1] - end[1]) < 0.0003)
        return json(res, 400, {
          error:
            "The pins are too close. Choose a destination at least a block away.",
        });
      return json(res, 200, await route(start, end));
    }
    const dist = path.join(root, "dist");
    const decoded = decodeURIComponent(u.pathname);
    let target = path.resolve(dist, "." + decoded);
    if (!target.startsWith(dist + path.sep) && target !== dist) {
      res.writeHead(403);
      return res.end();
    }
    if (!fs.existsSync(target) || fs.statSync(target).isDirectory())
      target = path.join(dist, "index.html");
    if (!fs.existsSync(target))
      return json(res, 404, {
        error: "Start the development UI on port 5481, or run npm run build.",
      });
    const types = {
      ".html": "text/html",
      ".js": "text/javascript",
      ".css": "text/css",
      ".json": "application/json",
      ".svg": "image/svg+xml",
      ".png": "image/png",
    };
    res.writeHead(200, {
      "Content-Type": types[path.extname(target)] || "application/octet-stream",
      "Referrer-Policy": "strict-origin-when-cross-origin",
    });
    fs.createReadStream(target).pipe(res);
  } catch (e) {
    json(res, 502, {
      error:
        e.name === "TimeoutError"
          ? "The routing service took too long. Retry, or use the saved sample route."
          : e.message || "Request failed.",
    });
  }
});
server.listen(Number(process.env.PORT || 8788), process.env.HOST || "127.0.0.1", () =>
  console.log(
    `Useless Speed API ready on ${process.env.HOST || "127.0.0.1"}:${process.env.PORT || 8788} (${addressCount} addresses, ${placeCount} places)`,
  ),
);
