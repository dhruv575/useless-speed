import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def available(relative):
    path = ROOT / relative
    if not path.is_file():
        raise SystemExit(f"Missing {relative}. Run git lfs pull to retrieve the research data.")
    with path.open("rb") as stream:
        if stream.read(43).startswith(b"version https://git-lfs.github.com/spec/v1"):
            raise SystemExit(f"{relative} is a Git LFS pointer. Run git lfs pull first.")
    return path


def read_json(relative):
    return json.loads(available(relative).read_text(encoding="utf-8"))


def write_json(output, data):
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {path} ({len(data['features'])} features)")
