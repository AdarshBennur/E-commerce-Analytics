#!/usr/bin/env python3
"""
pipeline/create_sample_dataset.py
==================================
Streaming sampler — converts the raw 9 GB CSV into a ~100 K-row sample
without ever loading more than a single line into memory.

100 K rows is the right balance for a portfolio analytics dashboard:
  • Realistic distributions across all event types, categories, and brands
  • Covers all 30 days of November (uniform temporal spread)
  • Pipeline runs in < 5 s, analytics tables stay < 1 MB
  • Runtime memory stays well under 512 MB

Strategy: systematic (every-Nth-row) sampling.
  - Scans the file line-by-line through a large OS read buffer.
  - Writes every STEP-th data row, preserving the header.
  - Stops as soon as TARGET_ROWS is reached.

Two modes (set SPREAD_SAMPLE below):
  SPREAD_SAMPLE = True  →  every STEP-th row across the full file
                            → uniform distribution, reads full ~9 GB once
                            → ~10 s on a modern laptop
  SPREAD_SAMPLE = False →  first TARGET_ROWS rows (< 1 s, early-November only)
"""

import os
import sys
import time

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE  = os.path.join(ROOT, "data",        "2019-Nov.csv")
OUTPUT_DIR  = os.path.join(ROOT, "data_sample")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "2019-Nov-sample.csv")

TARGET_ROWS   = 100_000    # how many data rows to write (100 K is optimal for this dashboard)
SPREAD_SAMPLE = True       # True = spread across full file; False = take first N rows

# ~58 M rows in the 9 GB November file → take every 580th row for a 100 K sample.
ESTIMATED_TOTAL_ROWS = 58_000_000
STEP = max(1, ESTIMATED_TOTAL_ROWS // TARGET_ROWS)   # ≈ 580

# 64 MB read / write buffers — keeps system-call overhead negligible
IO_BUF = 64 * 1024 * 1024

# ─── GUARDS ───────────────────────────────────────────────────────────────────
if __name__ != "__main__":
    raise ImportError(
        "pipeline/create_sample_dataset.py must be run as a script, not imported."
    )


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}]  {msg}", flush=True)


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    log("=" * 60)
    log("Streaming CSV sampler")
    log(f"  Input  : {INPUT_FILE}")
    log(f"  Output : {OUTPUT_FILE}")
    log(f"  Target : {TARGET_ROWS:,} rows")
    log(f"  Mode   : {'spread (every %d-th row)' % STEP if SPREAD_SAMPLE else 'head (first %d rows)' % TARGET_ROWS}")
    log("=" * 60)

    if not os.path.isfile(INPUT_FILE):
        print(f"\nERROR: Input file not found: {INPUT_FILE}", file=sys.stderr)
        print("Expected the raw November CSV at data/2019-Nov.csv", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    file_size_gb = os.path.getsize(INPUT_FILE) / 1e9
    log(f"  Source size: {file_size_gb:.1f} GB")

    t0 = time.time()
    written = 0
    read_lines = 0

    with (
        open(INPUT_FILE,  "r", encoding="utf-8", errors="replace", buffering=IO_BUF) as fin,
        open(OUTPUT_FILE, "w", encoding="utf-8", buffering=IO_BUF) as fout,
    ):
        # Always copy the header row unchanged
        header = fin.readline()
        if not header:
            print("ERROR: Input file is empty.", file=sys.stderr)
            sys.exit(1)
        fout.write(header)

        if not SPREAD_SAMPLE:
            # ── Fast path: copy the first TARGET_ROWS data rows ────────────────
            log("Reading first 1 M rows (fast path)…")
            for line in fin:
                if not line.strip():
                    continue
                fout.write(line)
                written += 1
                if written >= TARGET_ROWS:
                    break
                if written % 100_000 == 0:
                    elapsed = time.time() - t0
                    log(f"  … {written:,} rows written  ({elapsed:.1f}s)")
        else:
            # ── Spread path: take every STEP-th row ────────────────────────────
            log(f"Spread sampling: keeping every {STEP}-th row…")
            for line in fin:
                if not line.strip():
                    continue
                read_lines += 1
                if read_lines % STEP == 0:
                    fout.write(line)
                    written += 1
                    if written >= TARGET_ROWS:
                        break
                    if written % 100_000 == 0:
                        elapsed = time.time() - t0
                        log(f"  … {written:,} rows written  (scanned {read_lines:,})  ({elapsed:.1f}s)")

    elapsed = time.time() - t0
    out_size_mb = os.path.getsize(OUTPUT_FILE) / 1e6

    log("")
    log("=" * 60)
    log(f"✓  Sample dataset created")
    log(f"   Rows written : {written:,}")
    log(f"   Output size  : {out_size_mb:.1f} MB")
    log(f"   Time elapsed : {elapsed:.1f}s")
    log(f"   Location     : {OUTPUT_FILE}")
    log("=" * 60)

    return written


if __name__ == "__main__":
    main()
