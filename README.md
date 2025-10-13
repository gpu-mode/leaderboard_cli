# Leaderboard CLI

A command-line interface tool for submitting kernel implementations to BackendBench. This tool streamlines the submission process for both single kernel files and batch submissions from directories.

## Features

- Submit single kernel implementations with detailed metadata
- Batch submit multiple kernels from a directory structure
- Local SQLite database for tracking submissions
- View and filter submission history
- Support for remote API endpoints (optional)

## Installation

### From source

```bash
# Clone the repository
cd leaderboard_cli

# Install the package in development mode (installs all dependencies automatically)
pip install -e .
```

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

### `leaderboard submit`

Submit kernel implementation(s) to BackendBench.

**Options:**
- `--op, --operation`: Operation type (e.g., add, mul, matmul) - Required for single file
- `--overload`: Overload type (e.g., Tensor, Float, Int) - Optional
- `--dsl`: DSL type (e.g., cutedsl, triton, cuda) - **Required**
- `--device`: Device type (e.g., A100, H100, V100) - **Required**
- `--file`: Path to a single kernel file
- `--directory`: Path to directory containing multiple kernels
- `--endpoint`: API endpoint URL (default: http://localhost:8000/submit)
- `--local-only`: Store submissions locally only without sending to remote endpoint (default: True)

### `leaderboard list`

List submitted kernels from the local database.

**Options:**
- `--op, --operation`: Filter by operation type
- `--dsl`: Filter by DSL type
- `--device`: Filter by device type
- `--limit`: Maximum number of results (default: 20)
- `--show-content`: Display file content in the output

### `leaderboard show`

Show details of a specific submission by ID.

**Arguments:**
- `submission_id`: The ID of the submission to display

## Submission Modes

The CLI supports two modes for handling submissions:

### Local-Only Mode (Default)

By default, all submissions are stored **only** in your local SQLite database. No network requests are made.

```bash
# Local-only (default)
leaderboard submit --dsl triton --device A100 --file kernel.py
```

**What happens:**
- ✅ File is stored in local database (`~/.leaderboard/submissions.db`)
- ❌ No network request is made
- ✅ Works completely offline

### Remote Submission Mode

Optionally, you can also send submissions to a remote API endpoint (e.g., a leaderboard server):

```bash
# Submit both locally AND to a remote server
leaderboard submit \
  --dsl triton \
  --device A100 \
  --file kernel.py \
  --local-only false \
  --endpoint https://your-server.com/api/submit
```

**What happens:**
- ✅ File is stored in local database (same as local-only mode)
- ✅ Also sends HTTP POST request to the specified endpoint
- ✅ You keep a local copy regardless of network status

**JSON sent to endpoint:**
```json
{
  "operation": "add",
  "overload": "Tensor",
  "dsl": "triton",
  "device": "A100",
  "file_name": "kernel.py",
  "file_content": "... full file content ..."
}
```

> **Note:** Remote submission requires a backend server at the specified endpoint. By default, no server is provided

## Data Storage

Submissions are stored in a local SQLite database at:
```
~/.leaderboard/submissions.db
```

Each submission includes:
- Operation type
- Overload type (if specified)
- DSL type
- Device type
- File name and content
- Original file path
- Timestamp
- Optional metadata

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
leaderboard list --op add --limit 5 --show-content
```

## Development

### Project Structure

```
leaderboard_cli/
├── leaderboard/
│   ├── __init__.py
│   ├── cli.py          # Main CLI interface
│   ├── database.py     # SQLite database management
│   └── submit.py       # Submission logic
├── examples/           # Example kernel files
├── pyproject.toml      # Project configuration and dependencies
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
