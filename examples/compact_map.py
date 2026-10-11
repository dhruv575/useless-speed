"""Export a prepared map layer; requires no Python packages or LFS download."""
import argparse
from _common import read_json, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--dataset", choices=["signals", "speed-limits", "observed-speeds", "stop-signs", "streets"], default="signals")
parser.add_argument("--hour", type=int, choices=range(24), default=17)
parser.add_argument("--output", default="outputs/signals.geojson")
args = parser.parse_args()
data = read_json(f"app/public/data/{args.dataset}.json")
if args.dataset == "observed-speeds":
    for feature in data["features"]:
        props = feature["properties"]
        props["speed_mph"] = props["speeds"].get(str(args.hour))
        props["hour"] = args.hour
        props["month"] = data["period"]
    data["features"] = [f for f in data["features"] if f["properties"]["speed_mph"] is not None]
write_json(args.output, data)
