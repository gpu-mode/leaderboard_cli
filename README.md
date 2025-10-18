# Leaderboard CLI

A command-line interface tool for submitting kernel implementations to BackendBench. This tool streamlines the submission process for both single kernel files and batch submissions from directories.

## Architecture

**Client-Server Model:**
- **CLI (Client)**: Submit kernels, view submissions
- **Server**: FastAPI server with SQLite database

## Features

- Submit single kernel implementations with detailed metadata
- Batch submit multiple kernels from a directory structure
- View and filter submission history from server
- Simple FastAPI server for receiving and storing submissions

## Installation

```bash
cd leaderboard_cli
pip install -e .
```

This installs both the CLI and server dependencies.

## Quick Start

### 1. Start the Server

```bash
cd server
python main.py
```

Server will run at `http://localhost:8000`

### 2. Authenticate

```bash
leaderboard login
```

You'll need a GitHub Personal Access Token:
- Generate at: https://github.com/settings/tokens
- Required scopes: `read:user`, `user:email`

### 3. Use the CLI

Open a new terminal:

## Usage

### Submit a Single Kernel

Submit a single kernel file with operation metadata:

```bash
leaderboard submit \
  --op add \
  --overload Tensor \
  --dsl cutedsl \
  --device A100 \
  --file add_implementation_v1.py
```

### Submit Multiple Kernels from Directory

Submit all kernels in a directory. The tool will automatically detect the operation and overload types from the directory structure:

```bash
leaderboard submit \
  --dsl triton \
  --device A100 \
  --directory generated_kernels/
```

Expected directory structure:
```
generated_kernels/
├── add/
│   ├── Tensor/
│   │   ├── add_v1.py
│   │   └── add_v2.py
│   └── Float/
│       └── add_v1.py
├── mul/
│   └── mul_v1.py
└── matmul/
    └── Tensor/
        └── matmul_optimized.py
```

### View Submissions

List all submissions:
```bash
leaderboard list
```

Filter by operation, DSL, or device:
```bash
leaderboard list --op add --dsl triton --limit 10
```

Show file content:
```bash
leaderboard list --show-content --limit 5
```

### View Specific Submission

Show details of a specific submission by ID:
```bash
leaderboard show 1
```

## Command Reference

### Authentication Commands

#### `leaderboard login`
Authenticate with GitHub Personal Access Token

#### `leaderboard logout`
Clear authentication and log out

#### `leaderboard whoami`
Show current authenticated user

### `leaderboard submit`

Submit kernel implementation(s) to the server. **Requires authentication.**

**Options:**
- `--op, --operation`: Operation type (e.g., add, mul, matmul) - Required for single file
- `--overload`: Overload type (e.g., Tensor, Float, Int) - Optional
- `--dsl`: DSL type (e.g., cutedsl, triton, cuda) - **Required**
- `--device`: Device type (e.g., A100, H100, V100) - **Required**
- `--file`: Path to a single kernel file
- `--directory`: Path to directory containing multiple kernels
- `--endpoint`: API endpoint URL (default: http://localhost:8000/api/submit)

### `leaderboard list`

List submitted kernels from the server.

**Options:**
- `--op, --operation`: Filter by operation type
- `--dsl`: Filter by DSL type
- `--device`: Filter by device type
- `--limit`: Maximum number of results (default: 20)
- `--endpoint`: API base URL (default: http://localhost:8000)

### `leaderboard show`

Show details of a specific submission by ID.

**Arguments:**
- `submission_id`: The ID of the submission to display

**Options:**
- `--endpoint`: API base URL (default: http://localhost:8000)

## How It Works

1. **User authenticates** → GitHub OAuth via Personal Access Token
2. **Server issues JWT** → Token stored locally in `~/.leaderboard/config.json`
3. **CLI submits kernels** → Sends HTTP POST with JWT Bearer token
4. **Server verifies & stores** → Links submission to user in database
5. **CLI queries server** → View all submissions via API

**Default endpoint:** `http://localhost:8000`

**Authentication:**
- Required for: Submissions
- Not required for: Viewing submissions

**Data stored on server:**
- User information (username, name, email from GitHub)
- Operation type
- Overload type (if specified)
- DSL type
- Device type
- File name and content
- Timestamp
- User who submitted

## Examples

### Example 1: Submit a CUDA kernel

```bash
leaderboard submit \
  --op matmul \
  --overload Tensor \
  --dsl cuda \
  --device A100 \
  --file kernels/matmul_optimized.cu
```

### Example 2: Submit Triton kernels from a directory

```bash
leaderboard submit \
  --dsl triton \
  --device H100 \
  --directory ./my_triton_kernels/
```

### Example 3: View recent submissions for a specific operation

```bash
leaderboard list --op add --limit 5
```

## Development

### Project Structure

```
leaderboard_cli/
├── leaderboard/          # CLI package
│   ├── __init__.py
│   ├── cli.py           # CLI commands
│   └── submit.py        # Submission logic
├── server/              # FastAPI server
│   ├── main.py          # Server implementation
│   ├── requirements.txt
│   └── README.md
├── examples/            # Example kernel files
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Contributing

## License

MIT License

