"""
Task 9 — Adaptive learning algorithms (pure functions, no DB).
Verifies Bayesian Knowledge Tracing and the Khan-style mastery ladder
behave correctly so that quiz performance can drive adaptation.
"""
from models.mastery import UserSkillMastery
from services.mastery_service import _update_bkt, _update_mastery_level


def _mastery(**kw):
    m = UserSkillMastery()
    # Explicit defaults (DB column defaults are not applied until flush).
    m.p_learned = kw.get("p_learned", 0.0)
    m.total_attempts = kw.get("total_attempts", 0)
    m.correct_attempts = kw.get("correct_attempts", 0)
    m.streak = kw.get("streak", 0)
    m.mastery_level = kw.get("mastery_level", "not_started")
    return m


def test_bkt_increases_on_correct_answer():
    m = _mastery(p_learned=0.4)
    _update_bkt(m, is_correct=True)
    assert m.p_learned > 0.4


def test_bkt_decreases_on_wrong_answer():
    m = _mastery(p_learned=0.6)
    _update_bkt(m, is_correct=False)
    assert m.p_learned < 0.6


def test_bkt_stays_within_bounds():
    m = _mastery(p_learned=0.99)
    for _ in range(10):
        _update_bkt(m, is_correct=True)
    assert 0.0 <= m.p_learned <= 1.0


def test_mastery_level_ladder():
    # mastered requires >=90% AND a streak of >=3
    m = _mastery(total_attempts=10, correct_attempts=10, streak=3)
    _update_mastery_level(m)
    assert m.mastery_level == "mastered"

    # high score but short streak -> only proficient
    m = _mastery(total_attempts=10, correct_attempts=10, streak=1)
    _update_mastery_level(m)
    assert m.mastery_level == "proficient"

    m = _mastery(total_attempts=10, correct_attempts=6, streak=0)
    _update_mastery_level(m)
    assert m.mastery_level == "familiar"

    m = _mastery(total_attempts=10, correct_attempts=2, streak=0)
    _update_mastery_level(m)
    assert m.mastery_level == "attempted"

    m = _mastery(total_attempts=0)
    _update_mastery_level(m)
    assert m.mastery_level == "not_started"


def test_single_correct_answer_is_not_proficient():
    """One correct answer must not look like mastery (conservative reporting)."""
    m = _mastery(total_attempts=1, correct_attempts=1, streak=1)
    _update_mastery_level(m)
    assert m.mastery_level == "attempted"


def test_conservative_progression_matches_report_table_7_1():
    """Consecutive correct answers climb gradually: attempted -> mastered."""
    expected = ["attempted", "familiar", "proficient", "mastered"]
    m = _mastery()
    got = []
    for _ in range(4):
        m.total_attempts += 1
        m.correct_attempts += 1
        m.streak += 1
        _update_mastery_level(m)
        got.append(m.mastery_level)
    assert got == expected


def test_wrong_answer_pulls_mastery_back_for_review():
    """A mastered learner who slips loses the 'mastered' label (streak reset)."""
    m = _mastery(total_attempts=5, correct_attempts=5, streak=5)
    _update_mastery_level(m)
    assert m.mastery_level == "mastered"

    # One wrong answer: streak resets (as update_skill_after_answer does).
    m.total_attempts += 1
    m.streak = 0
    _update_mastery_level(m)
    assert m.mastery_level != "mastered"
