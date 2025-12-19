from flask import Flask
from routes.health import health_bp
from routes.create_task import create_task_bp
from routes.manage_task import manage_task_bp

app = Flask(__name__)

# Load environment variables
from dotenv import load_dotenv
import os
load_dotenv()

# Load config
app.config['PLUGIN_SECRET'] = os.environ.get('PLUGIN_SECRET')
app.config['DATAHUB_API_URL'] = os.environ.get('DATAHUB_API_URL') 
app.config['PLUGIN_API_KEY'] = os.environ.get('PLUGIN_API_KEY')

@app.before_request
def log_request_info():
    import sys
    from flask import request
    # ANSI colors
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    
    # Get real IP if behind proxy (like ngrok)
    source_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"{GREEN}[REQUEST] SOURCE: {source_ip}{RESET}")
    print(f"{YELLOW}METHOD:{RESET} {request.method} {request.path}")
    print(f"{YELLOW}HEADERS:{RESET} {dict(request.headers)}")
    
    if request.is_json:
        print(f"{YELLOW}BODY (JSON):{RESET} {request.get_json(silent=True)}")
    elif request.get_data():
        print(f"{YELLOW}BODY (RAW):{RESET} {request.get_data(as_text=True)}")
    else:
        print(f"{YELLOW}BODY:{RESET} <EMPTY>")
    sys.stdout.flush()

@app.after_request
def log_response_info(response):
    import sys
    RED = '\033[91m'
    GREEN = '\033[92m'
    RESET = '\033[0m'
    
    color = GREEN if response.status_code < 400 else RED
    print(f"{color}[RESPONSE] STATUS: {response.status}{RESET}")
    sys.stdout.flush()
    return response

# Register Blueprints
app.register_blueprint(health_bp)
app.register_blueprint(create_task_bp)
app.register_blueprint(manage_task_bp)

@app.route('/frontend/index.js')
def serve_frontend_js():
    from flask import send_from_directory
    import os
    # Assuming frontend is one level up from backend/app.py
    # app.py is in backend/, frontend/ is in root/frontend/
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return send_from_directory(os.path.join(root_dir, 'frontend'), 'index.js')

if __name__ == '__main__':
    print("Starting backend app on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=True)
