"""
Task 3 — Preprocess text data using tokenization, stop-word removal,
and stemming techniques.
"""
from nlp.preprocessor import preprocess


def test_lowercases_and_strips_punctuation():
    out = preprocess("Hello, WORLD!!!")
    assert out == out.lower()
    assert "," not in out and "!" not in out


def test_removes_stopwords():
    # "the", "is", "a" are stopwords and should be dropped.
    out = preprocess("the cat is a programmer").split()
    assert "the" not in out
    assert "is" not in out


def test_applies_porter_stemming():
    # studies/studying -> "studi";  running/runs -> "run"
    assert "studi" in preprocess("studies studying").split()
    assert "run" in preprocess("running runs").split()


def test_question_words_are_preserved():
    # "what"/"how" are intentionally kept (they carry intent signal).
    tokens = preprocess("what is recursion and how does it work").split()
    assert "what" in tokens
    assert "how" in tokens


def test_compound_terms_split_on_hyphen():
    # "object-oriented" must become two tokens, not one.
    tokens = preprocess("object-oriented programming").split()
    assert "object" in tokens
    assert "orient" in tokens  # "oriented" -> "orient"


def test_empty_input_is_safe():
    assert preprocess("") == ""
    assert preprocess("   ") == ""
