# Testing Guide

This guide shows you how to test all the features of the Leaderboard CLI tool.

## 1. Verify Installation

First, make sure the CLI is installed correctly:

```bash
leaderboard --version
```

Expected output: `backendbench, version 0.1.0`

```bash
leaderboard --help
```

This should show all available commands: `submit`, `list`, and `show`.

## 2. Test Single Kernel Submission

Submit a single kernel file:

```bash
leaderboard submit \
  --op add \
  --overload Tensor \
  --dsl cutedsl \
  --device A100 \
  --file examples/single_kernel/add_implementation_v1.py
```

**Expected Output:**
```
╭─────────── Submission Successful ────────────╮
│ ✓ Successfully submitted kernel!            │
│                                              │
│ Submission ID: 1                             │
│ Operation: add                               │
│ DSL: cutedsl                                 │
│ Device: A100                                 │
│ File: add_implementation_v1.py               │
╰──────────────────────────────────────────────╯
```

## 3. Test Directory Submission

Submit all kernels from a directory:

```bash
leaderboard submit \
  --dsl triton \
  --device A100 \
  --directory examples/generated_kernels/
```

**Expected Output:**
```
Submission Summary:
Total files processed: 6
Successful: 6
Failed: 0

╭─────────────── Submission Details ───────────────╮
│ File                 │ Operation │ Status │ ID  │
├──────────────────────┼───────────┼────────┼─────┤
│ add_v1.py           │ add       │ ✓      │ 2   │
│ add_v2.py           │ add       │ ✓      │ 3   │
│ add_v1.py           │ add       │ ✓      │ 4   │
│ mul_v1.py           │ mul       │ ✓      │ 5   │
│ matmul_optimized.py │ matmul    │ ✓      │ 6   │
╰──────────────────────────────────────────────────╯
```

## 4. Test Listing Submissions

### List all submissions

```bash
leaderboard list
```

### List with filters

```bash
# Filter by operation
leaderboard list --op add

# Filter by DSL
leaderboard list --dsl triton

# Filter by device
leaderboard list --device A100

# Combine filters
leaderboard list --op add --dsl triton --limit 5
```

### List with content

```bash
leaderboard list --show-content --limit 3
```

This shows the file content for each submission (first 500 characters).

## 5. Test Viewing Specific Submission

```bash
leaderboard show 1
```

**Expected Output:**
```
Submission #1

╭────────────────────────────────────────╮
│ Operation  │ add                      │
│ Overload   │ Tensor                   │
│ DSL        │ cutedsl                  │
│ Device     │ A100                     │
│ File Name  │ add_implementation_v1.py │
│ Timestamp  │ 2025-10-13T...          │
╰────────────────────────────────────────╯

File Content:
╭────────────────────────────────────────╮
│ [full file content displayed here]     │
╰────────────────────────────────────────╯
```

## 6. Test Error Handling

### Missing required arguments

```bash
# Should fail - no --file or --directory
leaderboard submit --dsl triton --device A100
```

Expected: Error message about missing --file or --directory

```bash
# Should fail - no --op for single file
leaderboard submit --dsl triton --device A100 --file test.py
```

Expected: Error message about missing --op

### Invalid file path

```bash
leaderboard submit \
  --op add \
  --dsl triton \
  --device A100 \
  --file nonexistent.py
```

Expected: Error about file not found

## 7. Database Location

Check where submissions are stored:

```bash
ls -la ~/.leaderboard/
```

You should see `submissions.db` file.

## 8. Full Workflow Test

Here's a complete workflow to test everything:

```bash
# 1. Submit a single kernel
leaderboard submit \
  --op add \
  --overload Tensor \
  --dsl cutedsl \
  --device A100 \
  --file examples/single_kernel/add_implementation_v1.py

# 2. Submit directory of kernels
leaderboard submit \
  --dsl triton \
  --device A100 \
  --directory examples/generated_kernels/

# 3. List all submissions
leaderboard list

# 4. Filter by operation
leaderboard list --op add

# 5. View submission details
leaderboard show 1

# 6. List with content
leaderboard list --show-content --limit 2

# 7. Check help for each command
leaderboard submit --help
leaderboard list --help
leaderboard show --help
```

## 9. Clean Up (Optional)

To start fresh, you can delete the database:

```bash
rm -rf ~/.leaderboard/
```

The database will be recreated on the next submission.

## Testing Checklist

- [ ] `leaderboard --version` works
- [ ] `leaderboard --help` shows all commands
- [ ] Single file submission works
- [ ] Directory submission works  
- [ ] `list` command shows all submissions
- [ ] Filtering by --op, --dsl, --device works
- [ ] `show` command displays full submission details
- [ ] `--show-content` flag works
- [ ] Error messages are clear and helpful
- [ ] Database is created at `~/.leaderboard/submissions.db`

## Tips

- All commands support `--help` for detailed usage information
- The CLI uses rich formatting for beautiful terminal output
- All data is stored locally in SQLite (no network calls by default)
- You can submit the same file multiple times (useful for testing different versions)

