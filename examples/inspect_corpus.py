"""Explore the small catalog without downloading original documents."""
import json
from collections import Counter
from _common import read_json

catalog = read_json("corpus/derived/catalog.json")
unique = [row for row in catalog if not row["duplicate_of"]]
cards = read_json("corpus/derived/verified_timing_cards.json")
print(json.dumps({
    "source_records": len(catalog),
    "unique_source_files": len(unique),
    "unique_bytes": sum(row["bytes"] for row in unique),
    "categories": dict(Counter(row["category"] for row in unique)),
    "checked_card_documents": len(cards),
    "checked_intersections": sorted({row["intersection"] for row in cards}),
    "example_source": {k: unique[0][k] for k in ["id", "title", "source_url", "local_path", "sha256"]},
}, indent=2, ensure_ascii=False))
