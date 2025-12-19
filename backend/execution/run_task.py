import time
import json
import os

def run_task(subtask_id, config, input_files, work_dir):
    """
    Executes the plugin logic.

    Args:
        subtask_id (str): The ID of the task.
        config (dict): Configuration passed from the frontend.
        input_files (list): List of input files (if any).
        work_dir (str): The directory specifically created for this task's output.
    """
    print(f"[{subtask_id}] Running task with config: {config}")

    # --- YOUR BUSINESS LOGIC GOES HERE ---
    import requests
    
    # 1. Use Config
    # We will ignore the keyword for the image source (random), 
    # but we log it to show we read it.
    keyword = config.get("keyword", "random")
    print(f"[{subtask_id}] Searching for: {keyword}")

    # 2. Perform Work (Download an Image)
    # Using picsum.photos for a random reliable image
    image_url = "https://picsum.photos/400/300" 
    print(f"[{subtask_id}] Downloading image from {image_url}...")
    
    try:
        r = requests.get(image_url, timeout=10)
        r.raise_for_status()
        
        # 3. Save Result to Work Directory
        image_filename = "downloaded_image.jpg"
        image_path = os.path.join(work_dir, image_filename)
        
        with open(image_path, "wb") as f:
            f.write(r.content)
            
        print(f"[{subtask_id}] Image saved to {image_path}")
        
        # 4. Create Result Metadata
        result_data = {
            "status": "success",
            "message": f"Successfully downloaded image for '{keyword}'",
            "files": [image_filename] # Logic could list multiple
        }
        
    except Exception as e:
        print(f"[{subtask_id}] Logic Failed: {e}")
        raise e # Let the wrapper handle the failure reporting

    # Write Mandatory Result File
    result_path = os.path.join(work_dir, "result.json")
    with open(result_path, "w") as f:
        json.dump(result_data, f, indent=2)

    print(f"[{subtask_id}] Result generated at {result_path}.")
