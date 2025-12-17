from flask import Blueprint, jsonify, request
import threading
from execution.run_task import run_task
from datahub.auth import require_auth

create_task_bp = Blueprint('create_task_bp', __name__)

@create_task_bp.route('/api/plugin/create_task', methods=['POST'])
@require_auth
def create_task():
    # Get configuration from request body
    body = request.get_json() or {}
    subtask_id = body.get("subtask_id")
    config = body.get("config", {})
    input_files = body.get("input_files", [])
    
    # Run task in a separate thread to avoid blocking the response
    # We must capture the real app object to pass context to the thread
    from flask import current_app
    app = current_app._get_current_object()
    
    def run_with_context(sid, conf, files):
        with app.app_context():
            from datahub.client import DatahubClient
            import os
            import time
            
            client = DatahubClient()
            print(f"[Framework] Starting task {sid}")
            
            # 1. Update Status to RUNNING
            client.update_status(sid, "RUNNING", progress=0)
            
            # 2. Start Heartbeat Thread
            keep_running = True
            def heartbeat_worker():
                while keep_running:
                    time.sleep(30) # 30s heartbeat interval
                    client.heartbeat(sid, progress=50) # Generic progress
            
            hb_thread = threading.Thread(target=heartbeat_worker, daemon=True)
            hb_thread.start()
            
            try:
                # 3. Execute User Logic
                # The contract: run_task(subtask_id, config, input_files)
                # It should generate 'result.json' in the current directory
                from execution.run_task import run_task
                
                # Clean previous result if any
                if os.path.exists("result.json"):
                    os.remove("result.json")
                    
                run_task(sid, conf, files)
                
                # Stop heartbeat
                keep_running = False
                
                # 4. Upload Result
                if os.path.exists("result.json"):
                    print(f"[Framework] Uploading result.json for {sid}")
                    upload_res = client.upload_file(sid, "result.json")
                    
                    if upload_res:
                        # 5. Report Result
                        file_url = upload_res.get("file_url")
                        file_size = os.path.getsize("result.json")
                        
                        # Defaut stats if user didn't return any (we just check file presence)
                        result_meta = {
                            "file_name": "result.json",
                            "file_size": file_size,
                            "file_path": file_url,
                            "file_md5": "computed-by-upload-file", # upload_file could return this, or we skip
                            "result": {
                                "success": True,
                                "msg": "Task completed successfully"
                            }
                        }
                        client.report_result(sid, result_meta)
                    else:
                        print("[Framework] Upload failed, cannot report result")
                else:
                    print("[Framework] Error: run_task did not generate result.json")
                    # Optionally report failure here
                    
            except Exception as e:
                keep_running = False
                print(f"[Framework] Task failed: {e}")
                # client.update_status(sid, "FAILED") # Optional error handling

    task_thread = threading.Thread(target=run_with_context, args=(subtask_id, config, input_files))
    task_thread.start()
    
    return jsonify({"code": 0, "msg": "success"})
