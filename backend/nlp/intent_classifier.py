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
        with open(os.path.join(_MODEL_DIR, "intent_vectorizer.pkl"), "rb") as f:
            _vectorizer = pickle.load(f)
        with open(os.path.join(_MODEL_DIR, "intent_classifier.pkl"), "rb") as f:
            _classifier = pickle.load(f)


def classify_intent(text: str) -> tuple[str, float]:
    """Return (predicted_intent, confidence)."""
    _load()
    processed = preprocess(text)
    features = _vectorizer.transform([processed])
    probs = _classifier.predict_proba(features)[0]
    max_idx = np.argmax(probs)
    confidence = probs[max_idx]
    intent = _classifier.classes_[max_idx]
    return intent, float(confidence)
