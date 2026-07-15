"""
Manual CSV/JSON Import Script for EduBot Training

Use this when you manually download datasets from Kaggle
(without the Kaggle API). Supports CSV and JSON files.

Usage:
    # Import a CSV as domain training data (all rows get the same domain)
    python3 training/import_csv.py domain data/kaggle_raw/stackoverflow.csv \
        --text-col Title --label programming

    # Import a CSV where each row has its own domain label
    python3 training/import_csv.py domain data/kaggle_raw/questions.csv \
        --text-col question --label-col category \
        --label-map '{"python":"programming","math":"mathematics","physics":"science"}'

    # Import intent data
    python3 training/import_csv.py intent data/kaggle_raw/intents.csv \
        --text-col text --label-col intent

    # After importing, retrain:
    python3 training/train_models.py --augmented
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from training.kaggle_adapter import (
    import_from_csv,
    merge_with_existing,
    clean_text,
    load_data_file,
)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")


def main():
    parser = argparse.ArgumentParser(
        description="Import CSV/JSON data into EduBot training pipeline"
    )
    parser.add_argument(
        "type",
        choices=["domain", "intent"],
        help="Type of data to import: 'domain' or 'intent'",
    )
    parser.add_argument(
        "file",
        help="Path to CSV or JSON file to import",
    )
    parser.add_argument(
        "--text-col",
        required=True,
        help="Column name containing the text/question",
    )
    parser.add_argument(
        "--label-col",
        default=None,
        help="Column name containing labels (if each row has its own label)",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Fixed label for all rows (e.g., 'programming'). "
        "Use when all rows belong to one domain/intent.",
    )
    parser.add_argument(
        "--label-map",
        default=None,
        help='JSON string mapping source labels to EduBot labels. '
        'E.g.: \'{"python":"programming","algebra":"mathematics"}\'',
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=2000,
        help="Maximum rows to import (default: 2000)",
    )
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=500,
        help="Maximum examples per class after balancing (default: 500)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)

    if not args.label and not args.label_col:
        print("ERROR: Must provide either --label (fixed label) or --label-col (column name)")
        sys.exit(1)

    label_key = args.type  # "domain" or "intent"
    label_map = json.loads(args.label_map) if args.label_map else None

    # Load data
    print(f"\nImporting from: {args.file}")
    rows = load_data_file(args.file, args.text_col, args.label_col, args.max_rows)
    print(f"  Loaded {len(rows)} rows")

    # Convert to EduBot format
    entries = []
    for row in rows:
        text = clean_text(row["text"])
        if not text or len(text) < 5:
            continue

        if args.label:
            # Fixed label for all rows
            entries.append({"text": text, label_key: args.label})
        elif args.label_col:
            raw_label = row.get("label", "")
            if label_map:
                mapped = label_map.get(raw_label, label_map.get(raw_label.lower()))
                if not mapped:
                    continue
                entries.append({"text": text, label_key: mapped})
            else:
                entries.append({"text": text, label_key: raw_label})

    print(f"  Converted {len(entries)} entries")

    if not entries:
        print("ERROR: No valid entries found. Check column names and labels.")
        sys.exit(1)

    # Show distribution
    dist = {}
    for e in entries:
        label = e[label_key]
        dist[label] = dist.get(label, 0) + 1
    print(f"  Distribution: {json.dumps(dist)}")

    # Merge with existing data
    existing_file = os.path.join(DATA_DIR, f"{label_key}s.json")
    output_file = os.path.join(DATA_DIR, f"{label_key}s_augmented.json")

    print(f"\nMerging with existing: {existing_file}")
    merged = merge_with_existing(
        entries, existing_file, label_key, args.max_per_class
    )

    with open(output_file, "w") as f:
        json.dump(merged, f, indent=2)

    print(f"\nSaved to: {output_file}")
    print(f"Total: {len(merged)} examples")
    print(f"\nNext step: python3 training/train_models.py --augmented")


if __name__ == "__main__":
    main()
