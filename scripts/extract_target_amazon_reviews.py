"""Extract reviews for named Amazon products without storing the full category file.

The Amazon Reviews 2023 category archives are multi-gigabyte gzip streams.  This
script reads an archive once, retains only reviews whose ``parent_asin`` is in the
target list, and writes a compact JSONL file.  It is deliberately streaming: the
full 6 GB Electronics archive is never written to disk.
"""

from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import sys
import time
from pathlib import Path


SOURCE_URL = (
    "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/"
    "raw/review_categories/Electronics.jsonl.gz"
)

# Metadata candidates were verified from the official Electronics metadata.
TARGETS = {
    "B0C337TNGS": "Beats Powerbeats Pro Wireless Earbuds",
    "B0C338S8M7": "Beats Studio Buds True Wireless Earbuds",
    "B09PRC3WC5": "TOZO A1 Mini Wireless Earbuds",
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


def compact(record: dict) -> dict:
    result = {field: record.get(field) for field in KEEP_FIELDS}
    result["product_name"] = TARGETS[result["parent_asin"]]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", default=SOURCE_URL)
    parser.add_argument(
        "--input-gzip",
        type=Path,
        help="Optional complete local archive. Prefer this after a resumable download.",
    )
    parser.add_argument("--progress-every", type=int, default=500_000)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    seen = 0
    matched = 0
    matched_by_product = {asin: 0 for asin in TARGETS}
    started = time.monotonic()
    # A temporary suffix prevents a partial run from being mistaken for a finished
    # dataset. The final rename happens only after the gzip stream reaches EOF.
    partial = args.output.with_suffix(args.output.suffix + ".partial")
    download = None
    if args.input_gzip:
        if not args.input_gzip.is_file():
            raise SystemExit(f"Input file not found: {args.input_gzip}")
        input_stream = args.input_gzip.open("rb")
    else:
        # urllib's TLS handshake is unreliable against this particular UCSD mirror
        # on some Windows/Python builds. curl has already connected successfully.
        download = subprocess.Popen(
            [
                "curl.exe", "--fail", "--location", "--retry", "5",
                "--retry-delay", "4", "--connect-timeout", "30", "--output",
                "-", args.source,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        assert download.stdout is not None
        input_stream = download.stdout
    try:
        with input_stream, gzip.GzipFile(fileobj=input_stream) as gzipped, partial.open(
            "w", encoding="utf-8"
        ) as out_file:
            for raw_line in gzipped:
                seen += 1
                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                parent_asin = record.get("parent_asin")
                if parent_asin in TARGETS:
                    out_file.write(json.dumps(compact(record), ensure_ascii=False) + "\n")
                    matched += 1
                    matched_by_product[parent_asin] += 1
                if seen % args.progress_every == 0:
                    elapsed = time.monotonic() - started
                    print(
                        json.dumps(
                            {
                                "reviews_scanned": seen,
                                "reviews_matched": matched,
                                "matched_by_product": matched_by_product,
                                "elapsed_minutes": round(elapsed / 60, 1),
                            }
                        ),
                        flush=True,
                    )
        if download and download.wait() != 0:
            raise RuntimeError("curl could not complete the official source stream")
    except Exception:
        # Keep the partial data for diagnosis/recovery, but do not silently label it
        # as a complete extraction.
        print(f"Extraction stopped; partial output retained at {partial}", file=sys.stderr)
        raise
    finally:
        if download and download.poll() is None:
            download.kill()

    partial.replace(args.output)
    manifest = {
        "source_url": args.source,
        "target_products": TARGETS,
        "reviews_scanned": seen,
        "reviews_matched": matched,
        "matched_by_product": matched_by_product,
        "completed": True,
        "output": str(args.output),
    }
    args.output.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
