from flask import Blueprint, jsonify, g
from routes.auth import login_required
from services.progress_service import get_summary, get_domain_detail

progress_bp = Blueprint("progress", __name__, url_prefix="/api/progress")


@progress_bp.route("/summary", methods=["GET"])
@login_required
def summary():
    result = get_summary(g.user.id)
    return jsonify(result)


@progress_bp.route("/<domain>", methods=["GET"])
@login_required
def domain_detail(domain):
    valid_domains = ["programming", "mathematics", "science", "aptitude"]
    if domain not in valid_domains:
        return jsonify({"error": f"Invalid domain. Choose from: {valid_domains}"}), 400

    result = get_domain_detail(g.user.id, domain)
    return jsonify(result)
