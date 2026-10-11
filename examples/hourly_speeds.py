"""Stream a historical month/hour from the CSV and join its segment geometry."""
import argparse
import csv
import json
import re
from _common import available, read_json, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--month", default="2026-09", help="YYYY-MM")
parser.add_argument("--hour", type=int, choices=range(24), default=17)
parser.add_argument("--output", default="outputs/hourly-speeds.geojson")
args = parser.parse_args()
if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", args.month):
    parser.error("--month must be YYYY-MM")
segments = {str(s["cmp_segid"]): s for s in read_json("corpus/raw/sfcta/cmp_segments_exp.json")}
features, unmatched = [], 0
with available("corpus/derived/tables/inrix_rt_hourly_exp.csv").open(encoding="utf-8-sig", newline="") as stream:
    for row in csv.DictReader(stream):
        if row["date"] != args.month or row["period"].strip() != str(args.hour) or not row["avg_speed"]:
            continue
        segment = segments.get(row["cmp_segid"])
        if segment is None:
            unmatched += 1
            continue
        geometry = segment["geometry"]
        features.append({"type": "Feature", "geometry": json.loads(geometry) if isinstance(geometry, str) else geometry, "properties": {
            "cmp_segid": row["cmp_segid"], "name": segment["cmp_name"], "direction": segment["direction"],
            "month": args.month, "hour": args.hour, "speed_mph": float(row["avg_speed"]),
        }})
write_json(args.output, {"type": "FeatureCollection", "features": features})
print(f"{unmatched} observations lacked matching geometry; no interpolation or causal inference applied.")
