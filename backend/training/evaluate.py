"""Evaluate trained classifiers with detailed metrics."""
import json
import os
import pickle
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sklearn.metrics import classification_report, confusion_matrix
from nlp.preprocessor import preprocess

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "trained_models")


def evaluate_classifier(data_path: str, name: str):
    """Evaluate a trained classifier against its training data."""
    with open(data_path) as f:
        data = json.load(f)

    label_key = "domain" if "domain" in data[0] else "intent"
    texts = [preprocess(item["text"]) for item in data]
    labels = [item[label_key] for item in data]

    with open(os.path.join(MODEL_DIR, f"{name}_vectorizer.pkl"), "rb") as f:
        vectorizer = pickle.load(f)
    with open(os.path.join(MODEL_DIR, f"{name}_classifier.pkl"), "rb") as f:
        classifier = pickle.load(f)

    X = vectorizer.transform(texts)
    predictions = classifier.predict(X)

    print(f"\n{'='*60}")
    print(f"  {name.upper()} CLASSIFIER EVALUATION")
    print(f"{'='*60}")
    print(classification_report(labels, predictions))
    print("Confusion Matrix:")
    classes = sorted(set(labels))
    cm = confusion_matrix(labels, predictions, labels=classes)
    # Header
    print(f"{'':>15}", end="")
    for c in classes:
        print(f"{c:>12}", end="")
    print()
    for i, row_label in enumerate(classes):
        print(f"{row_label:>15}", end="")
        for val in cm[i]:
            print(f"{val:>12}", end="")
        print()


def main():
    print("Evaluating trained models...\n")
    evaluate_classifier(os.path.join(DATA_DIR, "domains.json"), "domain")
    evaluate_classifier(os.path.join(DATA_DIR, "intents.json"), "intent")


if __name__ == "__main__":
    main()
