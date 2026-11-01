"""Extract likely true-wireless-earbud products from a bounded metadata gzip segment."""

from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path


INCLUDE = re.compile(r"\b(?:earbuds?|airpods?|true[ -]?wireless|tws)\b", re.I)
WIRELESS = re.compile(r"\b(?:wireless|bluetooth|airpods?|true[ -]?wireless|tws)\b", re.I)
EXCLUDE = re.compile(
    r"\b(?:case|cover|holder|hook|tips?|replacement|adapter|charger|protector|"
    r"stand|rack|earmuffs?|cushion|skin|strap)\b",
    re.I,
)
DEVICE_SIGNAL = re.compile(
    r"\b(?:bluetooth|wireless|noise[ -]?cancel|anc|microphones?|mics?|"
    r"playtime|battery|music|audio|driver|sound|ipx\d|touch[ -]?control)\b",
    re.I,
)
KEEP = (
    "parent_asin",
    "title",
    "average_rating",
    "rating_number",
    "price",
    "store",
    "features",
    "categories",
    "details",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-gzip", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/earphone_products_pilot.jsonl")
    )
    args = parser.parse_args()
    if not args.input_gzip.is_file():
        raise SystemExit(f"Input file not found: {args.input_gzip}")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    scanned = 0
    kept = 0
    with args.input_gzip.open("rb") as compressed, gzip.GzipFile(
        fileobj=compressed, mode="rb"
    ) as gzipped, args.output.open("w", encoding="utf-8") as out_file:
        try:
            for line in gzipped:
                scanned += 1
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                title = record.get("title", "")
                if not (INCLUDE.search(title) and WIRELESS.search(title)):
                    continue
                accessory = EXCLUDE.search(title)
                device_signal = DEVICE_SIGNAL.search(title)
                # A device title may mention a charging case at the end. In contrast,
                # an accessory title usually introduces itself as a case/cover before
                # it presents any audio-device capability.
                if accessory and (not device_signal or accessory.start() < device_signal.start()):
                    continue
                compact = {key: record.get(key) for key in KEEP if key in record}
                out_file.write(json.dumps(compact, ensure_ascii=False) + "\n")
                kept += 1
        except EOFError:
            pass

    print(json.dumps({"records_scanned": scanned, "products_kept": kept, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
