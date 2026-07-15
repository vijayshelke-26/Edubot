"""
Train domain and intent classifiers, save as pickle files.

Usage:
    python3 training/train_models.py              # Auto-uses augmented data if available
    python3 training/train_models.py --original    # Force training on original data only
    python3 training/train_models.py --compare     # Train both and compare accuracy
"""
import json
import os
import pickle
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import SGDClassifier
from sklearn.svm import LinearSVC
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report
from nlp.preprocessor import preprocess

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "trained_models")

os.makedirs(MODEL_DIR, exist_ok=True)


def train_classifier(data_path: str, name: str, model_type: str = "nb"):
    """Train a TF-IDF + classifier and save it.

    Args:
        data_path: Path to JSON training data
        name: Model name prefix (e.g., 'domain', 'intent')
        model_type: 'nb' (Naive Bayes), 'svm' (Linear SVM), or 'sgd' (SGD)
    """
    with open(data_path) as f:
        data = json.load(f)

    label_key = "domain" if "domain" in data[0] else "intent"
    texts = [preprocess(item["text"]) for item in data]
    labels = [item[label_key] for item in data]

    print(f"  Dataset: {len(data)} examples, {len(set(labels))} classes")
    print(f"  Classes: {dict(sorted({l: labels.count(l) for l in set(labels)}.items()))}")

    # Adjust vectorizer for dataset size
    max_features = min(10000, max(5000, len(data) * 10))
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=max_features,
        sublinear_tf=True,  # Apply log normalization to TF
    )
    X = vectorizer.fit_transform(texts)

    # Select classifier
    if model_type == "svm":
        classifier = LinearSVC(C=1.0, max_iter=10000)
    elif model_type == "sgd":
        classifier = SGDClassifier(loss="modified_huber", max_iter=1000, random_state=42)
    else:
        classifier = MultinomialNB(alpha=0.1)

    classifier.fit(X, labels)

    # Cross-validation
    cv_folds = min(5, min(labels.count(l) for l in set(labels)))
    cv_folds = max(2, cv_folds)
    scores = cross_val_score(classifier, X, labels, cv=cv_folds, scoring="accuracy")
    print(f"  {name} ({model_type}) - {cv_folds}-fold CV: {scores.mean():.4f} (+/- {scores.std():.4f})")

    # If dataset is large enough, do a proper train/test split evaluation
    if len(data) >= 100:
        X_train, X_test, y_train, y_test = train_test_split(
            X, labels, test_size=0.2, random_state=42, stratify=labels
        )
        classifier_eval = type(classifier)(**classifier.get_params())
        classifier_eval.fit(X_train, y_train)
        test_acc = classifier_eval.score(X_test, y_test)
        print(f"  Hold-out test accuracy (80/20 split): {test_acc:.4f}")

    # Save models
    with open(os.path.join(MODEL_DIR, f"{name}_vectorizer.pkl"), "wb") as f:
        pickle.dump(vectorizer, f)
    with open(os.path.join(MODEL_DIR, f"{name}_classifier.pkl"), "wb") as f:
        pickle.dump(classifier, f)

    print(f"  Saved {name}_vectorizer.pkl and {name}_classifier.pkl")
    return scores.mean()


def compare_models(data_path: str, name: str):
    """Train multiple classifiers and compare their accuracy."""
    print(f"\n  Comparing models for {name}:")
    print(f"  {'Model':<20} {'CV Accuracy':>12}")
    print(f"  {'-'*20} {'-'*12}")

    with open(data_path) as f:
        data = json.load(f)

    label_key = "domain" if "domain" in data[0] else "intent"
    texts = [preprocess(item["text"]) for item in data]
    labels = [item[label_key] for item in data]

    max_features = min(10000, max(5000, len(data) * 10))
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=max_features,
        sublinear_tf=True,
    )
    X = vectorizer.fit_transform(texts)

    cv_folds = min(5, min(labels.count(l) for l in set(labels)))
    cv_folds = max(2, cv_folds)

    models = {
        "Naive Bayes": MultinomialNB(alpha=0.1),
        "Linear SVM": LinearSVC(C=1.0, max_iter=10000),
        "SGD Classifier": SGDClassifier(loss="modified_huber", max_iter=1000, random_state=42),
    }

    best_name = None
    best_score = 0

    for model_name, model in models.items():
        scores = cross_val_score(model, X, labels, cv=cv_folds, scoring="accuracy")
        mean_score = scores.mean()
        print(f"  {model_name:<20} {mean_score:>11.4f}")
        if mean_score > best_score:
            best_score = mean_score
            best_name = model_name

    print(f"\n  Best model: {best_name} ({best_score:.4f})")
    return best_name


def main():
    use_original = "--original" in sys.argv
    do_compare = "--compare" in sys.argv

    # Determine data files: prefer augmented data when available
    domain_augmented = os.path.join(DATA_DIR, "domains_augmented.json")
    intent_augmented = os.path.join(DATA_DIR, "intents_augmented.json")

    if use_original:
        domain_file = os.path.join(DATA_DIR, "domains.json")
        intent_file = os.path.join(DATA_DIR, "intents.json")
    else:
        domain_file = domain_augmented if os.path.exists(domain_augmented) else os.path.join(DATA_DIR, "domains.json")
        intent_file = intent_augmented if os.path.exists(intent_augmented) else os.path.join(DATA_DIR, "intents.json")

    use_augmented = "augmented" in domain_file or "augmented" in intent_file

    print("=" * 60)
    print("  EduBot NLP Model Training")
    print("=" * 60)
    print(f"  Data source: {'augmented (Kaggle)' if use_augmented else 'original'}")
    print(f"  Domain data: {domain_file}")
    print(f"  Intent data: {intent_file}")
    print()

    if do_compare:
        print("--- Domain Classifier ---")
        compare_models(domain_file, "domain")
        print("\n--- Intent Classifier ---")
        compare_models(intent_file, "intent")
        print("\nComparison complete. Run without --compare to train and save.")
        return

    print("--- Training Domain Classifier ---")
    domain_acc = train_classifier(domain_file, "domain")

    print("\n--- Training Intent Classifier ---")
    intent_acc = train_classifier(intent_file, "intent")

    print(f"\n{'=' * 60}")
    print(f"  Domain CV accuracy: {domain_acc:.1%}")
    print(f"  Intent CV accuracy: {intent_acc:.1%}")
    print(f"{'=' * 60}")
    print("Training complete!")


if __name__ == "__main__":
    main()
