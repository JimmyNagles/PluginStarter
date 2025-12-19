from flask import Blueprint, jsonify, request
import threading
import os
import shutil
from execution.run_task import run_task
from datahub.auth import require_auth

create_task_bp = Blueprint('create_task_bp', __name__)

# Global state for idempotency
ACTIVE_TASKS = set()
TASKS_LOCK = threading.Lock()

@create_task_bp.route('/api/plugin/create_task', methods=['POST'])
@require_auth
def create_task():
    # Get configuration from request body
    body = request.get_json() or {}
    subtask_id = body.get("subtask_id")
    config = body.get("config", {})
    input_files = body.get("input_files", [])
    
    print("[DEBUG] Received config:", config)
    
    # Idempotency Guard
    with TASKS_LOCK:
        if subtask_id in ACTIVE_TASKS:
            print(f"[Framework] Skipping duplicate task execution for {subtask_id}")
            return jsonify({"code": 0, "msg": "success"})
        ACTIVE_TASKS.add(subtask_id)
    
    # Run task in a separate thread to avoid blocking the response
    from flask import current_app
    app = current_app._get_current_object()
    
    def run_with_context(sid, conf, files):
        with app.app_context():
            from datahub.client import DatahubClient
            import time
            
            client = DatahubClient()
            print(f"[Framework] Starting task {sid}")
            
            # Setup Per-Task Working Directory
            work_dir = f"/tmp/datahub/{sid}"
            os.makedirs(work_dir, exist_ok=True)
            
            # Threading Event for Heartbeat Termination
            stop_heartbeat = threading.Event()
            
            def heartbeat_worker():
                # Wait 30s, then ping, repeat until stopped
                # wait() returns True if flag is set, False if timeout
                while not stop_heartbeat.wait(30):
                    client.heartbeat(sid, progress=50) 

            hb_thread = threading.Thread(target=heartbeat_worker, daemon=True)
            
            try:
                # 1. Update Status to RUNNING
                client.update_status(sid, "RUNNING", progress=0)
                
                # 2. Start Heartbeat
                hb_thread.start()

                # 3. Execute User Logic
                # clean old result if exists (redundant with new work_dir, but safe)
                result_file_path = os.path.join(work_dir, "result.json")
                if os.path.exists(result_file_path):
                    os.remove(result_file_path)
                    
                from execution.run_task import run_task
                run_task(sid, conf, files, work_dir)
                
                # 4. Upload Result
                if os.path.exists(result_file_path):
                    print(f"[Framework] Uploading result.json for {sid}")
                    upload_res = client.upload_file(sid, result_file_path)
                    
                    if upload_res:
                        # 5. Report Result
                        file_url = upload_res.get("file_url")
                        file_size = os.path.getsize(result_file_path)
                        
                        result_meta = {
                            "file_name": "result.json",
                            "file_size": file_size,
                            "file_path": file_url,
                            "file_md5": "computed-by-upload-file",
                            "result": {
                                "success": True,
                                "msg": "Task completed successfully"
                            }
                        }
                        client.report_result(sid, result_meta)
                        print(f"[Framework] Task {sid} completed successfully.")
                    else:
                        raise Exception("Upload failed, cannot report result")
                else:
                    raise Exception("run_task did not generate result.json")

            except Exception as e:
                print(f"[Framework] Task {sid} failed: {e}")
                # Explicit Failure Reporting
                try:
                    client.report_result(sid, {
                        "result": {
                            "success": False,
                            "msg": str(e)
                        }
                    })
                    # Also explicitly set status to FAILED in case result doesn't trigger it
                    client.update_status(sid, "FAILED")
                except Exception as inner_e:
                    print(f"[Framework] Failed to report error for {sid}: {inner_e}")
            
            finally:
                # Cleanup
                stop_heartbeat.set()
                hb_thread.join(timeout=1)
                
                # Remove from active tasks
                with TASKS_LOCK:
                    ACTIVE_TASKS.discard(sid)
                    
                # Optional: Cleanup /tmp directory (commented out for debugging)
                # shutil.rmtree(work_dir, ignore_errors=True)

    task_thread = threading.Thread(target=run_with_context, args=(subtask_id, config, input_files))
    task_thread.start()
    
    return jsonify({"code": 0, "msg": "success"})
