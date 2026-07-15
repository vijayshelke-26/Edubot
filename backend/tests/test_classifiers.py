"""
Tasks 4, 5 & 10 — NLP models (NLTK + scikit-learn Naive Bayes) and
"test chatbot accuracy". Asserts the trained intent classifier meets an
accuracy bar and predicts representative utterances correctly.
"""
import json
import os

import pytest

from nlp.intent_classifier import classify_intent
from nlp.domain_classifier import classify_domain

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

ACCURACY_THRESHOLD = 0.85  # measured ~0.96; guards against regressions


def _load(name):
    with open(os.path.join(DATA_DIR, f"{name}.json")) as f:
        return json.load(f)


def test_intent_classifier_accuracy_meets_threshold():
    data = _load("intents")
    correct = sum(1 for item in data if classify_intent(item["text"])[0] == item["intent"])
    accuracy = correct / len(data)
    assert accuracy >= ACCURACY_THRESHOLD, f"intent accuracy {accuracy:.3f} < {ACCURACY_THRESHOLD}"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("hello there", "greeting"),
        ("hi, good morning", "greeting"),
        ("goodbye, see you later", "farewell"),
        ("can you quiz me please", "request_quiz"),
        ("show me my progress", "check_progress"),
        ("thank you so much", "thanks"),
    ],
)
def test_intent_classifier_known_utterances(text, expected):
    intent, conf = classify_intent(text)
    assert intent == expected, f"{text!r} -> {intent} (conf={conf:.2f})"


def test_intent_confidence_is_a_probability():
    _, conf = classify_intent("what is a variable")
    assert 0.0 <= conf <= 1.0


def test_domain_classifier_returns_known_label():
    domain, conf = classify_domain("how do python for loops work")
    assert domain in {"programming", "general"}
    assert 0.0 <= conf <= 1.0
