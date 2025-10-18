"""FastAPI server for receiving kernel submissions."""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

from auth import verify_github_token, create_access_token, verify_token

app = FastAPI(title="Leaderboard API")

# Database setup
DB_PATH = Path(__file__).parent / "submissions.db"


@contextmanager
def get_db():
    """Database connection context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    with get_db() as conn:
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                username TEXT NOT NULL,
                name TEXT,
                email TEXT,
                avatar_url TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(provider, provider_id)
            )
        """)
        
        # Submissions table with user tracking
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                operation TEXT NOT NULL,
                overload TEXT,
                dsl TEXT NOT NULL,
                device TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()


# Initialize database on startup
init_db()


class GitHubAuthRequest(BaseModel):
    """Schema for GitHub authentication request."""
    github_token: str


class KernelSubmission(BaseModel):
    """Schema for kernel submission."""
    operation: str
    overload: Optional[str] = None
    dsl: str
    device: str
    file_name: str
    file_content: str


@app.post("/api/auth/github")
async def auth_github(auth_request: GitHubAuthRequest):
    """Authenticate user with GitHub token."""
    try:
        # Verify GitHub token and get user info
        user_info = await verify_github_token(auth_request.github_token)
        
        # Store or update user in database
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("""
                SELECT id FROM users 
                WHERE provider = ? AND provider_id = ?
            """, (user_info["provider"], user_info["provider_id"]))
            
            existing_user = cursor.fetchone()
            
            if existing_user:
                user_id = existing_user["id"]
                # Update user info
                cursor.execute("""
                    UPDATE users 
                    SET username = ?, name = ?, email = ?, avatar_url = ?
                    WHERE id = ?
                """, (
                    user_info["username"],
                    user_info["name"],
                    user_info["email"],
                    user_info["avatar_url"],
                    user_id
                ))
            else:
                # Create new user
                cursor.execute("""
                    INSERT INTO users 
                    (provider, provider_id, username, name, email, avatar_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_info["provider"],
                    user_info["provider_id"],
                    user_info["username"],
                    user_info["name"],
                    user_info["email"],
                    user_info["avatar_url"],
                    datetime.now().isoformat()
                ))
                user_id = cursor.lastrowid
            
            conn.commit()
        
        # Create JWT token
        access_token = create_access_token({
            "user_id": user_id,
            "username": user_info["username"],
            "provider": user_info["provider"]
        })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "username": user_info["username"],
                "name": user_info["name"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/submit")
async def submit_kernel(
    submission: KernelSubmission,
    user: dict = Depends(verify_token)
):
    """Accept a kernel submission and store it in the database. Requires authentication."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO submissions 
                (user_id, operation, overload, dsl, device, file_name, file_content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user["user_id"],
                submission.operation,
                submission.overload,
                submission.dsl,
                submission.device,
                submission.file_name,
                submission.file_content,
                datetime.now().isoformat()
            ))
            conn.commit()
            submission_id = cursor.lastrowid
        
        return {
            "success": True,
            "id": submission_id,
            "message": "Kernel submitted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/submissions")
async def list_submissions(
    operation: Optional[str] = None,
    dsl: Optional[str] = None,
    device: Optional[str] = None,
    limit: int = 20
):
    """List submissions with optional filters."""
    query = """
        SELECT s.*, u.username, u.name as user_name
        FROM submissions s
        JOIN users u ON s.user_id = u.id
        WHERE 1=1
    """
    params = []
    
    if operation:
        query += " AND s.operation = ?"
        params.append(operation)
    if dsl:
        query += " AND s.dsl = ?"
        params.append(dsl)
    if device:
        query += " AND s.device = ?"
        params.append(device)
    
    query += " ORDER BY s.timestamp DESC LIMIT ?"
    params.append(limit)
    
    with get_db() as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
    return {
        "count": len(rows),
        "submissions": [dict(row) for row in rows]
    }


@app.get("/api/submissions/{submission_id}")
async def get_submission(submission_id: int):
    """Get a specific submission by ID."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT s.*, u.username, u.name as user_name
            FROM submissions s
            JOIN users u ON s.user_id = u.id
            WHERE s.id = ?
        """, (submission_id,))
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return dict(row)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Leaderboard API",
        "endpoints": {
            "submit": "POST /api/submit",
            "list": "GET /api/submissions",
            "get": "GET /api/submissions/{id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

