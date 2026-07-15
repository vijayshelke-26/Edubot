from flask import Blueprint, request, jsonify, g
from routes.auth import login_required
from services.quiz_service import get_quiz_history
from services.adaptive_quiz_service import start_adaptive_quiz, submit_adaptive_quiz
from services.mastery_service import get_all_mastery

quiz_bp = Blueprint("quiz", __name__, url_prefix="/api/quiz")


@quiz_bp.route("/start", methods=["GET"])
@login_required
def start_quiz():
    result = start_adaptive_quiz(g.user.id)
    if not result["questions"]:
        return jsonify({"error": "No quiz questions available"}), 404
    return jsonify(result)


@quiz_bp.route("/submit", methods=["POST"])
@login_required
def submit():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    answers = data.get("answers")
    if not answers:
        return jsonify({"error": "Answers are required"}), 400

    result = submit_adaptive_quiz(g.user.id, answers)
    return jsonify(result)


@quiz_bp.route("/history", methods=["GET"])
@login_required
def history():
    attempts = get_quiz_history(g.user.id)
    return jsonify({"attempts": attempts})


@quiz_bp.route("/mastery", methods=["GET"])
@login_required
def mastery():
    skills = get_all_mastery(g.user.id)
    return jsonify({"skills": skills})
