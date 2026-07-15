from flask import Blueprint, request, jsonify, g
from routes.auth import login_required
from models import db
from models.chat import ChatSession, ChatMessage
from services.chat_service import handle_message

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.route("/message", methods=["POST"])
@login_required
def send_message():
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "Message is required"}), 400

    result = handle_message(
        user_id=g.user.id,
        text=data["message"],
        session_id=data.get("session_id"),
    )
    return jsonify(result)


@chat_bp.route("/sessions", methods=["GET"])
@login_required
def list_sessions():
    sessions = (
        ChatSession.query.filter_by(user_id=g.user.id)
        .order_by(ChatSession.started_at.desc())
        .all()
    )
    return jsonify({"sessions": [s.to_dict() for s in sessions]})


@chat_bp.route("/sessions/<int:session_id>/messages", methods=["GET"])
@login_required
def get_messages(session_id):
    session = ChatSession.query.filter_by(
        id=session_id, user_id=g.user.id
    ).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    messages = (
        ChatMessage.query.filter_by(session_id=session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return jsonify({"messages": [m.to_dict() for m in messages]})


@chat_bp.route("/messages/<int:message_id>/feedback", methods=["POST"])
@login_required
def submit_feedback(message_id):
    data = request.get_json() or {}
    value = data.get("feedback")
    if value not in (1, -1, 0, None):
        return jsonify({"error": "feedback must be 1, -1, or 0"}), 400

    msg = (
        ChatMessage.query.join(ChatSession)
        .filter(ChatMessage.id == message_id, ChatSession.user_id == g.user.id)
        .first()
    )
    if not msg:
        return jsonify({"error": "Message not found"}), 404
    if msg.role != "bot":
        return jsonify({"error": "Feedback only allowed on bot messages"}), 400

    msg.feedback = value if value in (1, -1) else None
    db.session.commit()
    return jsonify({"message": msg.to_dict()})


@chat_bp.route("/feedback/stats", methods=["GET"])
@login_required
def feedback_stats():
    rows = (
        db.session.query(ChatMessage.feedback, db.func.count(ChatMessage.id))
        .join(ChatSession)
        .filter(ChatSession.user_id == g.user.id, ChatMessage.role == "bot")
        .group_by(ChatMessage.feedback)
        .all()
    )
    counts = {"up": 0, "down": 0, "none": 0}
    for value, count in rows:
        if value == 1:
            counts["up"] = count
        elif value == -1:
            counts["down"] = count
        else:
            counts["none"] = count
    total_rated = counts["up"] + counts["down"]
    counts["satisfaction_rate"] = (
        round(counts["up"] / total_rated, 3) if total_rated else None
    )
    return jsonify(counts)
