import requests
import json
import time
from flask import current_app
from datahub.auth import generate_signature

class DatahubClient:
    def __init__(self):
        # We access config at call time via current_app to ensure we get latest/context-bound config
        pass

    def _post(self, endpoint, data):
        """
        Helper to send signed POST requests to DataHub.
        """
        api_url = current_app.config.get('DATAHUB_API_URL')
        api_key = current_app.config.get('PLUGIN_API_KEY')
        secret = current_app.config.get('PLUGIN_SECRET')
        
        if not api_url or not api_key or not secret:
            print("[DataHubClient] Error: Missing configuration (URL, Key, or Secret)")
            return None

        url = f"{api_url}{endpoint}"
        # IMPORANT: sort_keys=True and separators=(',', ':') are required for consistent signing per spec
        body_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        timestamp = str(int(time.time())) # Spec says unix timestamp (seconds)
        signature = generate_signature(secret, body_str, timestamp)

        headers = {
            "Content-Type": "application/json",
            "D-API-KEY": api_key,
            "D-TIMESTAMP": timestamp,
            "D-SIGNATURE": signature
        }

        try:
            response = requests.post(url, data=body_str, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[DataHubClient] Request failed for {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[DataHubClient] Server response: {e.response.text}")
            return None

    def update_status(self, subtask_id, status, progress=None):
        """
        Updates the status of a task in DataHub.
        POST /api/task/update_status
        """
        print(f"[DataHub] Updating status for {subtask_id} to {status} (Progress: {progress})")
        payload = {
            "subtask_id": subtask_id,
            "status": status
        }
        if progress is not None:
            payload["progress"] = progress
            
        self._post("/api/task/update_status", payload)

    def heartbeat(self, subtask_id, progress=None):
        """
        Sends a heartbeat to DataHub.
        POST /api/task/heartbeat
        """
        print(f"[DataHub] Heartbeat for {subtask_id} (Progress: {progress})")
        payload = {
            "subtask_id": subtask_id,
            "timestamp": int(time.time()),
            "process": progress
        }
        self._post("/api/task/heartbeat", payload)

    def upload_init(self, subtask_id, filename, filesize, chunk_size=None):
        """
        Initialize multipart upload.
        POST /api/task/upload/init
        """
        payload = {
            "subtask_id": subtask_id,
            "filename": filename,
            "filesize": filesize
        }
        if chunk_size:
            payload["chunk_size"] = chunk_size
            
        resp = self._post("/api/task/upload/init", payload)
        if resp and resp.get("code") == 0:
            return resp.get("data")
        return None

    def upload_complete(self, subtask_id, filename, upload_id, parts):
        """
        Complete multipart upload.
        POST /api/task/upload/complete
        """
        payload = {
            "upload_id": upload_id,
            "subtask_id": subtask_id,
            "filename": filename,
            "parts": parts
        }
        resp = self._post("/api/task/upload/complete", payload)
        if resp and resp.get("code") == 0:
            return resp.get("data")
        return None

    def report_result(self, subtask_id, result_metadata):
        """
        Submit final task result.
        POST /api/task/result
        """
        payload = result_metadata.copy()
        payload["subtask_id"] = subtask_id
        
        self._post("/api/task/result", payload)

    def upload_file(self, subtask_id, file_path):
        """
        Orchestrates the full field upload process:
        1. init -> get upload_url(s)
        2. PUT file parts to upload_url(s)
        3. complete -> get final file_url
        """
        import os
        import hashlib

        print(f"[DataHub] Starting upload for {file_path}")
        
        if not os.path.exists(file_path):
            print(f"[DataHub] Error: File {file_path} not found")
            return None

        filesize = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        # Calculate MD5 (optional but good practice)
        # file_md5 = hashlib.md5(open(file_path, 'rb').read()).hexdigest()

        # 1. Init Upload
        # For simplicity, we use 5MB chunks or just single file if small. 
        # But allow DataHub to decide chunking or we hint it.
        # Template simplicity: Let's assume single chunk for small dummy files.
        # Passing None for chunk_size implies backend decides or single part.
        init_data = self.upload_init(subtask_id, filename, filesize)
        if not init_data:
            print("[DataHub] Upload init failed")
            return None

        upload_id = init_data.get("upload_id")
        parts_urls = init_data.get("part_upload_urls", [])
        
        # 2. Upload Parts
        parts_etags = []
        with open(file_path, 'rb') as f:
            for part in parts_urls:
                index = part["index"]
                url = part["url"]
                
                # In a real chunked scenario, we'd seek and read specific bytes.
                # Here assuming single part for simplicity of this starter template logic.
                # If multiple parts, we need Logic to slice 'f'.
                # For this step, we just read the whole file for the first part (assuming it fits).
                content = f.read() 
                
                print(f"[DataHub] Uploading part {index} to {url}")
                try:
                    # Direct PUT to storage (presigned URL), usually no auth headers needed or specific ones.
                    # Standard S3 presigned PUT.
                    put_resp = requests.put(url, data=content)
                    put_resp.raise_for_status()
                    etag = put_resp.headers.get('ETag')
                    parts_etags.append({"index": index, "etag": etag})
                except Exception as e:
                    print(f"[DataHub] Part upload failed: {e}")
                    return None

        # 3. Complete Upload
        result = self.upload_complete(subtask_id, filename, upload_id, parts_etags)
        if result:
            print(f"[DataHub] Upload successful: {result.get('file_url')}")
            return result
        return None
