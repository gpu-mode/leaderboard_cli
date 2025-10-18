# Leaderboard Server

FastAPI server for receiving and storing kernel submissions.

## Installation

All dependencies are installed with the main package:

```bash
cd ..
pip install -e .
```

## Running the Server

```bash
# Development
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`

## API Endpoints

### POST /api/submit
Submit a kernel implementation

**Request body:**
```json
{
  "operation": "add",
  "overload": "Tensor",
  "dsl": "triton",
  "device": "A100",
  "file_name": "kernel.py",
  "file_content": "... file content ..."
}
```

**Response:**
```json
{
  "success": true,
  "id": 1,
  "message": "Kernel submitted successfully"
}
```

### GET /api/submissions
List submissions with optional filters

**Query parameters:**
- `operation` (optional)
- `dsl` (optional)
- `device` (optional)
- `limit` (default: 20)

### GET /api/submissions/{id}
Get a specific submission by ID

## Database

SQLite database stored at `server/submissions.db`

