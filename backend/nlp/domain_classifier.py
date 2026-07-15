import pickle
import os
import numpy as np
from nlp.preprocessor import preprocess

_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "trained_models")
_vectorizer = None
_classifier = None


def _load():
    global _vectorizer, _classifier
    if _vectorizer is None:
        with open(os.path.join(_MODEL_DIR, "domain_vectorizer.pkl"), "rb") as f:
            _vectorizer = pickle.load(f)
        with open(os.path.join(_MODEL_DIR, "domain_classifier.pkl"), "rb") as f:
            _classifier = pickle.load(f)


def classify_domain(text: str) -> tuple[str, float]:
    """Return (predicted_domain, confidence). Falls back to 'general' if confidence < 0.4."""
    _load()
    processed = preprocess(text)
    features = _vectorizer.transform([processed])
    probs = _classifier.predict_proba(features)[0]
    max_idx = np.argmax(probs)
    confidence = probs[max_idx]
    domain = _classifier.classes_[max_idx]

    if confidence < 0.4:
        return "general", confidence

    return domain, float(confidence)
