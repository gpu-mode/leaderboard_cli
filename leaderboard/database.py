"""Database module for storing kernel submissions."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class SubmissionDB:
    """SQLite database for storing kernel submissions."""
    
    def __init__(self, db_path: str = None):
        """Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to ~/.leaderboard/submissions.db
        """
        if db_path is None:
            db_dir = Path.home() / ".leaderboard"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "submissions.db")
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                overload TEXT,
                dsl TEXT NOT NULL,
                device TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_content TEXT NOT NULL,
                file_path TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)
        self.conn.commit()
    
    def add_submission(
        self,
        operation: str,
        dsl: str,
        device: str,
        file_name: str,
        file_content: str,
        overload: Optional[str] = None,
        file_path: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """Add a new kernel submission to the database.
        
        Args:
            operation: The operation type (e.g., 'add', 'mul')
            dsl: The DSL type (e.g., 'cutedsl', 'triton')
            device: The device type (e.g., 'A100', 'H100')
            file_name: Name of the submitted file
            file_content: Content of the kernel file
            overload: Optional overload type (e.g., 'Tensor')
            file_path: Optional original file path
            metadata: Optional additional metadata as a dictionary
            
        Returns:
            The ID of the inserted submission
        """
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO submissions 
            (operation, overload, dsl, device, file_name, file_content, file_path, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (operation, overload, dsl, device, file_name, file_content, file_path, timestamp, metadata_json))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_submissions(
        self,
        operation: Optional[str] = None,
        dsl: Optional[str] = None,
        device: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Retrieve submissions from the database.
        
        Args:
            operation: Filter by operation type
            dsl: Filter by DSL type
            device: Filter by device type
            limit: Maximum number of results to return
            
        Returns:
            List of submission dictionaries
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM submissions WHERE 1=1"
        params = []
        
        if operation:
            query += " AND operation = ?"
            params.append(operation)
        if dsl:
            query += " AND dsl = ?"
            params.append(dsl)
        if device:
            query += " AND device = ?"
            params.append(device)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_submission_by_id(self, submission_id: int) -> Optional[Dict]:
        """Get a specific submission by ID.
        
        Args:
            submission_id: The submission ID
            
        Returns:
            Submission dictionary or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def close(self):
        """Close the database connection."""
        self.conn.close()

