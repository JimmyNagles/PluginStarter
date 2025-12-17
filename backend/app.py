from flask import Flask
from routes.health import health_bp
from routes.create_task import create_task_bp
from routes.manage_task import manage_task_bp

app = Flask(__name__)
# Load config
app.config['PLUGIN_SECRET'] = 'my-secret-key' # Default for local testing
app.config['DATAHUB_API_URL'] = 'http://localhost:8000' # Default to mock
app.config['PLUGIN_API_KEY'] = 'dummy-plugin-key'

# Register Blueprints
app.register_blueprint(health_bp)
app.register_blueprint(create_task_bp)
app.register_blueprint(manage_task_bp)

if __name__ == '__main__':
    print("Starting backend app on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=True)
