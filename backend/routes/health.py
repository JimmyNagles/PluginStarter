from flask import Blueprint, jsonify
from datahub.auth import require_auth

health_bp = Blueprint('health_bp', __name__)

@health_bp.route('/api/plugin/health', methods=['GET'])
@require_auth
def health_check():
    return jsonify({"status": "ok"})
