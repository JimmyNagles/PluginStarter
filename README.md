# DataHub Plugin Starter Template

## What This Repository Is

This repository is a **production-ready starter template** for building DataHub plugins.

A DataHub plugin is not a traditional API or web app.
It is a **background worker service** that DataHub orchestrates.

DataHub controls:
*   task creation
*   lifecycle
*   retries
*   status updates
*   result delivery

Your plugin:
*   runs the job
*   writes output files
*   exits

This template hides all protocol complexity so you can focus on **business logic only**.

## What You Build With This Template

Every DataHub plugin has two parts:

```
DataHub Dashboard
 ├── loads Plugin Config JS (frontend)
 └── calls Plugin Backend (worker service)
```

1.  **Frontend (JavaScript)**
    *   Renders the task configuration UI inside the DataHub dashboard
    *   Returns a JSON config object
    *   Runs in the browser

2.  **Backend (Python / Flask)**
    *   Executes the task asynchronously
    *   Reports progress and results back to DataHub
    *   **Never returns results via HTTP responses**

## Repository Structure

```
datahub-plugin-starter/
├── frontend/
│   └── index.js              # Plugin config UI (browser)
│
├── backend/
│   ├── app.py                # Server entrypoint (framework)
│   ├── routes/               # API endpoints (framework)
│   │   ├── create_task.py
│   │   ├── manage_task.py
│   │   └── health.py
│   ├── datahub/              # DataHub protocol layer (framework)
│   │   ├── auth.py
│   │   └── client.py
│   ├── execution/
│   │   └── run_task.py       # ✅ THE ONLY FILE YOU EDIT
│   └── requirements.txt
│
└── README.md
```

### Frozen Core (Important)

The following files implement the DataHub protocol and should generally **not be modified**:
*   `backend/app.py`
*   `backend/routes/*`
*   `backend/datahub/*`

They handle:
*   request authentication (HMAC)
*   task lifecycle
*   heartbeats
*   multipart uploads
*   result reporting
*   background execution

**If you change these, you are changing the protocol.**

## The One File You Edit

**`backend/execution/run_task.py`**

This is the **only Python file** plugin authors edit.

**Execution contract:**

```python
def run_task(subtask_id, config, input_files):
    """
    subtask_id: unique ID assigned by DataHub
    config: JSON object returned by frontend/index.js
    input_files: list of file references provided by DataHub
    """
```

**Your responsibility inside `run_task.py`:**
1.  Read `config`
2.  Read `input_files` (if any)
3.  Perform your job (scraping, labeling, storage, validation, etc.)
4.  Write output file(s) to disk
5.  Return

**What you must not do:**
*   call DataHub APIs
*   manage task status
*   send heartbeats
*   upload files manually

**The framework handles all of that.**

## Runtime Workflow (How a Plugin Actually Runs)

This section describes the exact execution flow once a plugin is deployed and registered.

### 1. Trigger (Dashboard)
A user creates a task in the DataHub Dashboard and selects your plugin.
The plugin frontend (`frontend/index.js`) runs in the browser and returns a JSON configuration object.

### 2. Task Creation (DataHub Backend)
DataHub:
1.  creates a subtask
2.  signs the request
3.  sends a `POST` request to your backend:
    ```
    POST https://<plugin-service>/api/plugin/create_task
    ```

The request includes:
*   `subtask_id`
*   `config`
*   `input_files` (if any)

### 3. Authentication (Framework)
The framework verifies the HMAC signature using the shared secret.
Invalid requests are rejected automatically.

### 4. Supervisor Start (Framework)
The framework:
1.  immediately responds `200 OK` to DataHub
2.  spawns a background worker thread
3.  updates task status to `RUNNING`
4.  starts periodic heartbeats
5.  calls plugin logic:
    ```python
    run_task(subtask_id, config, input_files)
    ```

### 5. Plugin Logic Execution (Plugin Author)
Your code runs inside `run_task.py`:
1.  reads `config`
2.  processes `input_files`
3.  performs the job
4.  writes output file(s) (e.g. `result.json`, `result.zip`)
5.  returns

`run_task.py` does not manage lifecycle, uploads, or API calls.

### 6. Result Handling (Framework)
After `run_task` returns, the framework:
1.  stops heartbeats
2.  uploads output files using DataHub’s multipart upload flow (via presigned URLs)
3.  calls `/api/task/result` to report completion

### 7. Completion (Dashboard)
DataHub marks the task as **COMPLETED** and displays the result file(s) in the dashboard.

## Local Development

### Run the Backend

```bash
pip install -r backend/requirements.txt
python3 backend/app.py
```

Backend runs on:
`http://localhost:5002`

Verify:
```bash
curl http://localhost:5002/api/plugin/health
```

Expected:
```json
{ "status": "ok" }
```

### Exposing the Backend (Required for Dashboard Testing)

DataHub is a cloud platform and **cannot reach localhost**.

For local testing, expose your backend via HTTPS using a tunnel (e.g. `ngrok`):

```bash
ngrok http 5002
```

Use the generated HTTPS URL as your **Service URL** in the DataHub dashboard.

### Hosting the Frontend Config JS

`frontend/index.js` must be accessible via a **public HTTPS URL**.

Options:
*   S3 / OORT Storage (public)
*   GitHub Pages / raw file hosting
*   Any static hosting with correct `Content-Type: application/javascript`

This URL is your **Plugin Config JS URL**.

### Registering the Plugin in DataHub

In the DataHub dashboard:
1.  Create a new plugin
2.  Set:
    *   **Service URL** → your HTTPS backend URL
    *   **Config JS URL** → hosted `frontend/index.js`
3.  Save



## Analogy file by file

How Your Plugin Works: The "File-by-File" Journey


run_task.py
 seems simple, but it is the star of the show.

Here is the exact journey of a single task, from the moment DataHub calls you, to the moment you say "Done".

Step 1: The Doorway (
backend/app.py
)
This is your Server. It is always listening.

What it does: It receives the POST /create_task from DataHub.
Analogy: The Receptionist.
Code:
@app.route('/create_task') # "Someone is knocking!"
Step 2: The Manager (
backend/routes/create_task.py
)
This is the Supervisor. It takes the request from the Receptionist and organizes the work.

What it does:
Checks if this task ID is already running (Idempotency).
Creates a private folder for this task (/tmp/datahub/task-123).
Spawns a Background Thread so we can reply "OK" to DataHub immediately.
Calls 
run_task.py
.
Analogy: The Project Manager who assigns the work and handles the paperwork.
Step 3: The Worker (
backend/execution/run_task.py
)
This is YOU. This is the only code you theoretically need to write.

Does it do anything? YES! It does the actual job.
The Contract:
Input: Takes 
config
 (e.g. {"keyword": "cats"}).
Action: Scrapes web, processes data, generates images (yours currently just sleeps 2s and writes dummy data, but this is where the magic would be).
Output: It MUST write a file called result.json to its folder.
Code:
def run_task(sid, config, work_dir):
    # 1. Do work (Simulated by sleep)
    time.sleep(2)
    
    # 2. Write Result
    with open(f"{work_dir}/result.json", "w") as f:
         json.dump(..., f)
Analogy: The Specialist who sits in a room, does the work, puts the result in a box, and leaves.
Step 4: The Messenger (
backend/datahub/client.py
)
This is the Courier.

What it does:
Update Status: Tells DataHub "We are Running!".
Upload: Takes the result.json box from 
run_task.py
 and uploads it to the Cloud.
Report: Tells DataHub "Task Complete! Here is the file URL."
Analogy: The Fedex Driver who delivers the package back to headquarters.
Summary
app.py
 answers the phone.
create_task.py
 sets up the desk and hires the worker.
run_task.py
 (You) does the work and writes result.json.
client.py
 mails the result back.

