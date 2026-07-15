"""
Kaggle Dataset Adapter for EduBot Training

Downloads and converts Kaggle datasets into EduBot's training format.
Supports multiple dataset sources for both domain and intent classification.

Usage:
    pip install kaggle
    # Set up Kaggle API credentials (~/.kaggle/kaggle.json)
    python3 training/kaggle_adapter.py

Supported datasets (auto-downloaded):
    1. Domain classification:
       - "Stack Overflow Questions" (programming)
       - "Mathematics Dataset" (mathematics)
       - "SciQ - Science Questions" (science)
       - Custom aptitude datasets

    2. Intent classification:
       - "Chatbot NLU Evaluation" / "Intent Classification" datasets
"""

import csv
import json
import os
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
KAGGLE_RAW_DIR = os.path.join(DATA_DIR, "kaggle_raw")
os.makedirs(KAGGLE_RAW_DIR, exist_ok=True)


# ─── Dataset Registry ────────────────────────────────────────────────────────

DOMAIN_DATASETS = {
    # Dataset slug → (filename inside zip, text_column, label_column, label_map)
    "stackoverflow-questions": {
        "slug": "imoore/60k-stack-overflow-questions-with-quality-rate",
        "file": "train.csv",
        "text_col": "Title",
        "domain": "programming",
        "max_rows": 2000,
    },
    "sciq-science": {
        "slug": "thedevastator/sciq-a-dataset-for-science-question-answering",
        "file": "train.csv",
        "text_col": "question",
        "domain": "science",
        "max_rows": 2000,
    },
    "math-questions": {
        "slug": "thedevastator/grade-school-math-8k-q-a",
        "file": "main_train.csv",
        "text_col": "question",
        "domain": "mathematics",
        "max_rows": 2000,
    },
}

INTENT_DATASETS = {
    "chatbot-intents": {
        "slug": "elvinagammed/chatbots-intent-recognition-dataset",
        "file": None,
        "text_col": "text",
        "label_col": "intent",
        "max_rows": 3000,
    },
    "nlu-benchmark": {
        "slug": "hassanamin/atis-airlinetravelinformationsystem",
        "file": None,
        "text_col": "query",
        "label_col": "intent",
        "max_rows": 2000,
    },
}


# ─── Intent Mapping ──────────────────────────────────────────────────────────

# Map external intent labels to EduBot's 7 intents
INTENT_MAP = {
    # Greetings
    "greet": "greeting",
    "greeting": "greeting",
    "hello": "greeting",
    "hi": "greeting",
    # Farewells
    "goodbye": "farewell",
    "bye": "farewell",
    "farewell": "farewell",
    # Questions / Information
    "ask": "ask_question",
    "ask_question": "ask_question",
    "question": "ask_question",
    "inform": "ask_question",
    "search": "ask_question",
    "find": "ask_question",
    "define": "ask_question",
    "explain": "ask_question",
    "what": "ask_question",
    "how": "ask_question",
    "request": "ask_question",
    # Thanks
    "thank": "thanks",
    "thanks": "thanks",
    "thankyou": "thanks",
    "thank_you": "thanks",
    "appreciate": "thanks",
    # Help
    "help": "help",
    "assist": "help",
    "support": "help",
    "options": "help",
    # Affirmation / Confirmation (map to thanks as closest)
    "affirm": "thanks",
    "confirm": "thanks",
    "yes": "thanks",
    # Denial (map to help)
    "deny": "help",
    "no": "help",
    "cancel": "help",
}


# ─── Download Functions ──────────────────────────────────────────────────────

def check_kaggle_api():
    """Check if kaggle API is available."""
    try:
        import kaggle  # noqa: F401
        return True
    except ImportError:
        print("ERROR: kaggle package not installed.")
        print("  Install with: pip install kaggle")
        print("  Then set up credentials: https://www.kaggle.com/docs/api")
        return False
    except Exception as e:
        if "Could not find kaggle.json" in str(e):
            print("ERROR: Kaggle API credentials not found.")
            print("  1. Go to https://www.kaggle.com/settings → API → Create New Token")
            print("  2. Save the downloaded kaggle.json to ~/.kaggle/kaggle.json")
            print("  3. Run: chmod 600 ~/.kaggle/kaggle.json")
            return False
        raise


def download_dataset(slug: str, dest_dir: str) -> str | None:
    """Download a Kaggle dataset and return the extraction path."""
    from kaggle.api.kaggle_api_extended import KaggleApi

    extract_dir = os.path.join(dest_dir, slug.replace("/", "_"))
    if os.path.exists(extract_dir) and os.listdir(extract_dir):
        print(f"  Already downloaded: {slug}")
        return extract_dir

    os.makedirs(extract_dir, exist_ok=True)
    print(f"  Downloading: {slug} ...")
    try:
        api = KaggleApi()
        api.authenticate()
        api.dataset_download_files(slug, path=extract_dir, unzip=True)
        print(f"  Downloaded to: {extract_dir}")
        return extract_dir
    except Exception as e:
        print(f"  Failed to download {slug}: {e}")
        return None


def find_data_file(directory: str, preferred_name: str = None) -> str | None:
    """Find the most likely data file in a directory."""
    if preferred_name:
        path = os.path.join(directory, preferred_name)
        if os.path.exists(path):
            return path

    # Search recursively for CSV and JSON files
    for ext in ["*.csv", "*.json", "*.jsonl"]:
        files = list(Path(directory).rglob(ext))
        if files:
            # Prefer files with 'train' in the name
            train_files = [f for f in files if "train" in f.name.lower()]
            if train_files:
                return str(train_files[0])
            return str(files[0])

    return None


# ─── Data Loading Functions ──────────────────────────────────────────────────

def load_csv_data(filepath: str, text_col: str, label_col: str = None,
                  max_rows: int = None) -> list[dict]:
    """Load data from a CSV file."""
    rows = []
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)

            # Find the matching column (case-insensitive)
            if reader.fieldnames is None:
                return rows

            col_map = {c.lower().strip(): c for c in reader.fieldnames}
            actual_text_col = col_map.get(text_col.lower(), text_col)
            actual_label_col = col_map.get(
                label_col.lower(), label_col
            ) if label_col else None

            for i, row in enumerate(reader):
                if max_rows and i >= max_rows:
                    break

                text = row.get(actual_text_col, "").strip()
                if not text or len(text) < 5:
                    continue

                entry = {"text": text}
                if actual_label_col and actual_label_col in row:
                    entry["label"] = row[actual_label_col].strip().lower()

                rows.append(entry)

    except Exception as e:
        print(f"  Error reading {filepath}: {e}")

    return rows


def load_json_data(filepath: str, text_col: str, label_col: str = None,
                   max_rows: int = None) -> list[dict]:
    """Load data from a JSON file."""
    rows = []
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        # Handle both list-of-dicts and nested structures
        if isinstance(data, dict):
            # Look for a list inside
            for key, val in data.items():
                if isinstance(val, list):
                    data = val
                    break

        if not isinstance(data, list):
            return rows

        count = 0
        for item in data:
            if not isinstance(item, dict):
                continue

            raw_text = item.get(text_col, "")
            label_val = item.get(label_col, "") if label_col else ""

            # Handle nested format: {"intent": "Greeting", "text": ["Hi", "Hello"]}
            if isinstance(raw_text, list):
                texts = raw_text
            else:
                texts = [raw_text]

            if isinstance(label_val, str):
                label_val = label_val.strip().lower()

            for text in texts:
                if max_rows and count >= max_rows:
                    break
                if not isinstance(text, str):
                    continue
                text = text.strip()
                if not text or len(text) < 5:
                    continue

                entry = {"text": text}
                if label_col and label_val:
                    entry["label"] = label_val
                rows.append(entry)
                count += 1

            if max_rows and count >= max_rows:
                break

    except Exception as e:
        print(f"  Error reading {filepath}: {e}")

    return rows


def load_data_file(filepath: str, text_col: str, label_col: str = None,
                   max_rows: int = None) -> list[dict]:
    """Load data from CSV or JSON based on extension."""
    if filepath.endswith(".csv"):
        return load_csv_data(filepath, text_col, label_col, max_rows)
    elif filepath.endswith(".json") or filepath.endswith(".jsonl"):
        return load_json_data(filepath, text_col, label_col, max_rows)
    return []


# ─── Processing Functions ────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Clean a text string for training."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Truncate very long texts
    if len(text) > 300:
        text = text[:300]
    return text


def process_domain_datasets() -> list[dict]:
    """Download and process domain classification datasets from Kaggle."""
    print("\n=== Processing Domain Datasets ===\n")
    all_entries = []

    for name, config in DOMAIN_DATASETS.items():
        print(f"Processing: {name}")
        extract_dir = download_dataset(config["slug"], KAGGLE_RAW_DIR)
        if not extract_dir:
            continue

        data_file = find_data_file(extract_dir, config.get("file"))
        if not data_file:
            print(f"  No data file found in {extract_dir}")
            continue

        print(f"  Using file: {data_file}")
        rows = load_data_file(
            data_file, config["text_col"], max_rows=config["max_rows"]
        )

        domain = config["domain"]
        entries = []
        for row in rows:
            text = clean_text(row["text"])
            if text and len(text) >= 10:
                entries.append({"text": text, "domain": domain})

        print(f"  Extracted {len(entries)} examples for domain '{domain}'")
        all_entries.extend(entries)

    return all_entries


def process_intent_datasets() -> list[dict]:
    """Download and process intent classification datasets from Kaggle."""
    print("\n=== Processing Intent Datasets ===\n")
    all_entries = []

    for name, config in INTENT_DATASETS.items():
        print(f"Processing: {name}")
        extract_dir = download_dataset(config["slug"], KAGGLE_RAW_DIR)
        if not extract_dir:
            continue

        data_file = find_data_file(extract_dir, config.get("file"))
        if not data_file:
            print(f"  No data file found in {extract_dir}")
            continue

        print(f"  Using file: {data_file}")
        rows = load_data_file(
            data_file,
            config["text_col"],
            config["label_col"],
            config["max_rows"],
        )

        entries = []
        unmapped = set()
        for row in rows:
            text = clean_text(row["text"])
            label = row.get("label", "")

            # Map external intent to our intents
            mapped_intent = INTENT_MAP.get(label)
            if not mapped_intent:
                # Try partial matching
                for key, val in INTENT_MAP.items():
                    if key in label:
                        mapped_intent = val
                        break

            if mapped_intent and text and len(text) >= 3:
                entries.append({"text": text, "intent": mapped_intent})
            elif label:
                unmapped.add(label)

        if unmapped:
            print(f"  Unmapped intents (skipped): {unmapped}")
        print(f"  Extracted {len(entries)} examples")
        all_entries.extend(entries)

    return all_entries


# ─── Merge & Balance Functions ───────────────────────────────────────────────

def balance_dataset(entries: list[dict], label_key: str,
                    max_per_class: int = 500) -> list[dict]:
    """Balance a dataset so no class dominates. Caps each class at max_per_class."""
    import random

    by_class = {}
    for entry in entries:
        label = entry[label_key]
        by_class.setdefault(label, []).append(entry)

    balanced = []
    for label, items in by_class.items():
        if len(items) > max_per_class:
            random.seed(42)
            items = random.sample(items, max_per_class)
        balanced.extend(items)

    random.seed(42)
    random.shuffle(balanced)
    return balanced


def merge_with_existing(kaggle_entries: list[dict], existing_path: str,
                        label_key: str, max_per_class: int = 500) -> list[dict]:
    """Merge Kaggle data with existing hand-crafted data."""
    # Load existing data
    existing = []
    if os.path.exists(existing_path):
        with open(existing_path) as f:
            existing = json.load(f)

    print(f"  Existing data: {len(existing)} examples")
    print(f"  Kaggle data: {len(kaggle_entries)} examples")

    # Combine (existing data gets priority — it's higher quality)
    combined = existing + kaggle_entries

    # Remove duplicates (by lowercase text)
    seen = set()
    unique = []
    for entry in combined:
        text_lower = entry["text"].lower().strip()
        if text_lower not in seen:
            seen.add(text_lower)
            unique.append(entry)

    # Balance classes
    balanced = balance_dataset(unique, label_key, max_per_class)

    # Print distribution
    distribution = {}
    for entry in balanced:
        label = entry[label_key]
        distribution[label] = distribution.get(label, 0) + 1

    print(f"  Final dataset: {len(balanced)} examples")
    print(f"  Distribution: {json.dumps(distribution, indent=2)}")

    return balanced


# ─── CSV Import (Manual Datasets) ────────────────────────────────────────────

def import_from_csv(csv_path: str, text_col: str, label_col: str,
                    label_key: str, label_map: dict = None) -> list[dict]:
    """
    Import training data from a user-provided CSV file.

    This is for when you manually download a dataset from Kaggle
    instead of using the API.

    Args:
        csv_path: Path to the CSV file
        text_col: Column name containing the text
        label_col: Column name containing the label
        label_key: 'domain' or 'intent' (output key name)
        label_map: Optional dict mapping CSV labels to EduBot labels

    Returns:
        List of dicts in EduBot format
    """
    rows = load_csv_data(csv_path, text_col, label_col)
    entries = []

    for row in rows:
        text = clean_text(row["text"])
        label = row.get("label", "")

        if label_map:
            label = label_map.get(label, label_map.get(label.lower()))
            if not label:
                continue

        if text and len(text) >= 5:
            entries.append({"text": text, label_key: label})

    return entries


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    """Main function: download, process, merge, and save augmented training data."""

    if not check_kaggle_api():
        print("\n" + "=" * 60)
        print("ALTERNATIVE: Manual CSV Import")
        print("=" * 60)
        print("""
If you can't set up the Kaggle API, you can manually download
datasets and use the CSV import function:

    1. Download a dataset from Kaggle (as CSV)
    2. Place it in: backend/data/kaggle_raw/
    3. Run the import script:

       python3 -c "
       from training.kaggle_adapter import import_from_csv, merge_with_existing
       import json

       # Example: Import Stack Overflow questions as 'programming' domain
       entries = import_from_csv(
           csv_path='data/kaggle_raw/stackoverflow.csv',
           text_col='Title',
           label_col=None,  # No label column needed if all same domain
           label_key='domain',
           label_map=None
       )
       # Set domain for all entries
       for e in entries:
           e['domain'] = 'programming'

       # Merge with existing data
       merged = merge_with_existing(
           entries, 'data/domains.json', 'domain', max_per_class=500
       )

       # Save
       with open('data/domains_augmented.json', 'w') as f:
           json.dump(merged, f, indent=2)
       print(f'Saved {len(merged)} entries to data/domains_augmented.json')
       "
""")
        return

    # Process domain datasets
    kaggle_domains = process_domain_datasets()
    if kaggle_domains:
        merged_domains = merge_with_existing(
            kaggle_domains,
            os.path.join(DATA_DIR, "domains.json"),
            "domain",
            max_per_class=500,
        )
        output_path = os.path.join(DATA_DIR, "domains_augmented.json")
        with open(output_path, "w") as f:
            json.dump(merged_domains, f, indent=2)
        print(f"\nSaved augmented domain data to: {output_path}")

    # Process intent datasets
    kaggle_intents = process_intent_datasets()
    if kaggle_intents:
        merged_intents = merge_with_existing(
            kaggle_intents,
            os.path.join(DATA_DIR, "intents.json"),
            "intent",
            max_per_class=300,
        )
        output_path = os.path.join(DATA_DIR, "intents_augmented.json")
        with open(output_path, "w") as f:
            json.dump(merged_intents, f, indent=2)
        print(f"\nSaved augmented intent data to: {output_path}")

    print("\n" + "=" * 60)
    print("Next step: Retrain models with augmented data")
    print("=" * 60)
    print("  python3 training/train_models.py --augmented")


if __name__ == "__main__":
    main()
