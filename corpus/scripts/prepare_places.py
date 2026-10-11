"""Refresh the local SF place-name index from OpenStreetMap via Overpass.

Uses only the Python standard library. One bounded download is cached under
outputs/; search itself never calls a geocoding service. OSM data is ODbL 1.0.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
BOUNDS = [37.706, -122.525, 37.835, -122.345]  # south, west, north, east
ENDPOINT = "https://overpass-api.de/api/interpreter"
QUERY = """[out:json][timeout:25][maxsize:67108864][bbox:37.706,-122.525,37.835,-122.345];
(
  nwr["name"]["amenity"];
  nwr["name"]["shop"];
  nwr["name"]["tourism"];
  nwr["name"]["leisure"];
  nwr["name"]["historic"];
  nwr["name"]["office"];
  nwr["name"]["railway"="station"];
  nwr["name"]["natural"~"^(beach|peak)$"];
);
out center;"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Download again instead of using the cache")
    args = parser.parse_args()
    cache = ROOT / "outputs/osm-places.json"
    cache.parent.mkdir(exist_ok=True)
    if args.refresh or not cache.exists():
        print("Downloading named SF places from OpenStreetMap via Overpass...", flush=True)
        request = Request(ENDPOINT, data=urlencode({"data": QUERY}).encode(), headers={
            "User-Agent": "UselessSpeed/0.1 (https://github.com/dhruv575/useless-speed)",
        })
        with urlopen(request, timeout=90) as response:
            raw = response.read()
        payload = json.loads(raw)
        if payload.get("remark") or "elements" not in payload:
            raise RuntimeError(payload.get("remark", "Incomplete Overpass response"))
        cache.write_bytes(raw)
    payload = json.loads(cache.read_bytes())
    if payload.get("remark"):
        raise RuntimeError(payload["remark"])
    places = []
    for element in payload["elements"]:
        tags = element.get("tags", {})
        point = element.get("center", element)
        lat, lng = point.get("lat"), point.get("lon")
        if lat is None or lng is None or not (BOUNDS[0] <= lat <= BOUNDS[2] and BOUNDS[1] <= lng <= BOUNDS[3]):
            continue
        # Retain destinations, not parking areas or small street fixtures.
        if tags.get("amenity") in {"parking", "parking_space", "bicycle_parking", "bench", "waste_basket", "toilets", "drinking_water"}:
            continue
        if any(tags.get(k) == "yes" for k in ("disused", "abandoned", "demolished")):
            continue
        name = tags.get("name:en", tags.get("name", "")).strip()
        if not name:
            continue
        category = next((tags[k] for k in ("amenity", "shop", "tourism", "leisure", "historic", "office", "railway", "natural") if tags.get(k)), "place")
        address = " ".join(filter(None, [tags.get("addr:housenumber"), tags.get("addr:street")]))
        aliases = [tags[k] for k in ("name", "alt_name", "short_name", "official_name", "brand") if tags.get(k) and tags[k] != name]
        places.append({
            "id": f"osm:{element['type']}:{element['id']}",
            "label": name,
            "coordinates": [round(lng, 7), round(lat, 7)],
            "kind": "place",
            "category": category.replace("_", " "),
            "address": address,
            "aliases": aliases,
        })
    places.sort(key=lambda p: p["id"])
    destination = ROOT / "app/data/places.json"
    encoded = (json.dumps(places, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    destination.write_bytes(encoded)
    metadata = {
        "source": "OpenStreetMap contributors via Overpass API",
        "source_url": ENDPOINT,
        "source_timestamp": payload.get("osm3s", {}).get("timestamp_osm_base"),
        "downloaded_at": datetime.fromtimestamp(cache.stat().st_mtime, timezone.utc).isoformat(),
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "license": "ODbL-1.0",
        "license_url": "https://www.openstreetmap.org/copyright",
        "bounds_south_west_north_east": BOUNDS,
        "query": QUERY,
        "records": len(places),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "coordinates": "WGS84 longitude, latitude; way/relation bounding-box centers, not verified entrances",
        "limitations": "Community-maintained snapshot, not exhaustive or live. The router snaps points to roads.",
    }
    provenance = ROOT / "app/data/places-provenance.json"
    provenance.write_bytes((json.dumps(metadata, indent=2) + "\n").encode())
    manifest_path = ROOT / "corpus/snapshot-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact in (destination, provenance):
        relative = artifact.relative_to(ROOT).as_posix()
        manifest["files"] = [entry for entry in manifest["files"] if entry["path"] != relative]
        manifest["files"].append({
            "path": relative, "bytes": artifact.stat().st_size,
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        })
    manifest["places_supplement_date"] = metadata["source_timestamp"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"places": len(places), "bytes": len(encoded), "source_timestamp": metadata["source_timestamp"]}))


if __name__ == "__main__":
    main()
