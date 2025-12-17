import hmac
import hashlib
import time
import functools
from flask import request, jsonify, current_app

def generate_signature(secret, body, timestamp):
    """
    Generates HMAC-SHA256 signature.
    Signature = HMAC_SHA256(secret, body + timestamp)
    """
    message = (body + str(timestamp)).encode('utf-8')
    secret_bytes = secret.encode('utf-8')
    signature = hmac.new(secret_bytes, message, hashlib.sha256).hexdigest()
    return signature

def require_auth(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Check for required headers
        api_key = request.headers.get('D-API-KEY')
        signature = request.headers.get('D-SIGNATURE')
        timestamp = request.headers.get('D-TIMESTAMP')

        if not api_key or not signature or not timestamp:
            return jsonify({"code": 401, "msg": "Missing authentication headers"}), 401

        # 2. Verify timestamp (prevent replay attacks, window +/- 5 mins)
        try:
            ts = float(timestamp)
        except ValueError:
            return jsonify({"code": 401, "msg": "Invalid timestamp format"}), 401

        current_ts = time.time()
        if abs(current_ts - ts) > 300:
            return jsonify({"code": 401, "msg": "Request expired"}), 401

        # 3. Verify signature
        # For health check (GET), body is empty string usually, or we use request.data
        # Note: request.get_data(as_text=True) ensures we get the raw body string
        body = request.get_data(as_text=True)
        
        secret = current_app.config.get('PLUGIN_SECRET')
        if not secret:
             return jsonify({"code": 500, "msg": "Server misconfiguration: No secret"}), 500

        expected_signature = generate_signature(secret, body, timestamp)
        
        # Use hmac.compare_digest for constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(signature, expected_signature):
            return jsonify({"code": 401, "msg": "Invalid signature"}), 401
            
        return f(*args, **kwargs)
    return decorated_function
