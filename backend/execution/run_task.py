import time
import json

def run_task(subtask_id, config, input_files):
    """
    Executes the plugin logic.
    
    Args:
        subtask_id (str): The ID of the task.
        config (dict): Configuration passed from the frontend.
        input_files (list): List of input files (if any).
    """
    print(f"[{subtask_id}] Running task with config: {config}")
    
    # 1. Simulate Business Logic
    # e.g. Scraping, Processing, etc.
    time.sleep(2) # Simulate work
    
    # 2. Generate Output
    # The framework expects 'result.json' to be created.
    result_data = {
        "message": "Task completed successfully",
        "processed_config": config,
        "generated_at": time.time()
    }
    
    with open("result.json", "w") as f:
        json.dump(result_data, f, indent=2)
        
    print(f"[{subtask_id}] Result generated.")

