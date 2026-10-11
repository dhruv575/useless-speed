"""Verify bundled data against the recorded byte counts and SHA-256 digests."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POINTER = b"version https://git-lfs.github.com/spec/v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--available", action="store_true", help="Allow absent/LFS-only research files; app data remains required")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "corpus/snapshot-manifest.json").read_text(encoding="utf-8"))
    checked, skipped, problems = 0, [], []
    for entry in manifest["files"]:
        path = (ROOT / entry["path"]).resolve()
        if not path.is_relative_to(ROOT):
            problems.append(f"Path escapes repository: {entry['path']}")
            continue
        unavailable = not path.is_file()
        if not unavailable:
            with path.open("rb") as stream:
                unavailable = stream.read(len(POINTER)) == POINTER
        if unavailable:
            if args.available and entry["path"].startswith("corpus/"):
                skipped.append(entry["path"])
            else:
                problems.append(f"Missing data or Git LFS pointer: {entry['path']} (run git lfs pull)")
            continue
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if path.stat().st_size != entry["bytes"] or digest != entry["sha256"]:
            problems.append(f"Snapshot differs: {entry['path']}")
        checked += 1
    catalog = json.loads((ROOT / "corpus/derived/catalog.json").read_text(encoding="utf-8"))
    indexed = {e["path"]: e for e in manifest["files"]}
    for row in catalog:
        entry = indexed.get("corpus/" + row["local_path"])
        if not entry or entry["sha256"] != row["sha256"] or entry["bytes"] != row["bytes"]:
            problems.append(f"Catalog/manifest mismatch: {row['id']}")
    print(json.dumps({"verified_files": checked, "unavailable_research_files": len(skipped), "catalog_records": len(catalog), "problems": problems}, indent=2))
    raise SystemExit(bool(problems))


if __name__ == "__main__":
    main()
