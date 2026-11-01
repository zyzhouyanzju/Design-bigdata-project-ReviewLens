# -*- coding: utf-8 -*-
"""Extract target smartwatch reviews from Amazon Reviews'23 Electronics archive for cross-category validation."""

from __future__ import annotations

import gzip
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "raw" / "Electronics.jsonl.gz"
OUTPUT = ROOT / "data" / "raw" / "amazon_target_smartwatch_reviews.jsonl"

TARGETS = {
    "B0BLD1HN66": "Samsung Galaxy Watch 4",
    "B0BJW6R4YX": "Amazfit Bip U Pro",
    "B0BTV39NV3": "Garmin Venu Sq Music",
}

KEEP_FIELDS = (
    "parent_asin",
    "asin",
    "rating",
    "title",
    "text",
    "timestamp",
    "verified_purchase",
    "helpful_vote",
)


def main() -> None:
    started = time.monotonic()
    seen = 0
    matched = 0
    by_product = {k: 0 for k in TARGETS}
    max_lines = 12_000_000  # Scan 12M records (~60s) for substantial smartwatch sample

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(ARCHIVE, "rt", encoding="utf-8") as gz, OUTPUT.open("w", encoding="utf-8") as out:
        for line in gz:
            seen += 1
            if seen > max_lines:
                break
            if any(asin in line for asin in TARGETS):
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                pid = rec.get("parent_asin")
                if pid in TARGETS:
                    compact = {f: rec.get(f) for f in KEEP_FIELDS}
                    compact["product_name"] = TARGETS[pid]
                    out.write(json.dumps(compact, ensure_ascii=False) + "\n")
                    matched += 1
                    by_product[pid] += 1

    manifest = {
        "source_archive": str(ARCHIVE),
        "target_products": TARGETS,
        "records_scanned": seen,
        "reviews_matched": matched,
        "matched_by_product": by_product,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "output": str(OUTPUT),
    }
    manifest_path = OUTPUT.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

    # Copy to 提交项目/data/raw/
    submit_raw = ROOT / "提交项目" / "data" / "raw"
    if submit_raw.exists():
        shutil.copy2(OUTPUT, submit_raw / OUTPUT.name)
        shutil.copy2(manifest_path, submit_raw / manifest_path.name)

    # Run review_engine on smartwatch dataset
    out_engine = ROOT / "outputs" / "smartwatch_v2"
    out_topics = ROOT / "outputs" / "smartwatch_topics_v2"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "review_engine.run",
            "--input",
            str(OUTPUT),
            "--config",
            str(ROOT / "config" / "smartwatch.json"),
            "--output",
            str(out_engine),
            "--min-evidence",
            "10",
        ],
        cwd=str(ROOT),
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "review_engine.aspect_topics",
            "--evidence",
            str(out_engine / "evidence.csv"),
            "--config",
            str(ROOT / "config" / "smartwatch.json"),
            "--output",
            str(out_topics),
            "--clusters",
            "4",
            "--min-rows",
            "20",
        ],
        cwd=str(ROOT),
        check=True,
    )

    # Also copy outputs to 提交项目/outputs/
    submit_outputs = ROOT / "提交项目" / "outputs"
    if submit_outputs.exists():
        for src_dir in (out_engine, out_topics):
            dst_dir = submit_outputs / src_dir.name
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)


if __name__ == "__main__":
    main()
