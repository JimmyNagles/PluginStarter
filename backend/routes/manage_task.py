from flask import Blueprint, jsonify, request
from datahub.auth import require_auth

manage_task_bp = Blueprint('manage_task_bp', __name__)

@manage_task_bp.route('/api/plugin/manage_task', methods=['POST'])
@require_auth
def manage_task():
    # Placeholder: Do nothing, return success
    return jsonify({"code": 0, "msg": "success"})
