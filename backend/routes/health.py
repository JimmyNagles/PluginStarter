from flask import Blueprint, jsonify
from datahub.auth import require_auth

health_bp = Blueprint('health_bp', __name__)

import os

@health_bp.route('/api/plugin/health', methods=['GET'])
@require_auth
def health_check():
    return jsonify({
        "code": 0,
        "msg": "success",
        "status": "healthy",
        "plugin": {
            "version": os.getenv("PLUGIN_VERSION", "1.0.0"),
            "plugin_id": os.getenv("PLUGIN_ID", "test-plugin")
        }
    })
