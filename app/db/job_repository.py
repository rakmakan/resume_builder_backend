import sqlite3
from typing import List, Optional, Dict
from pathlib import Path
from app.models import Job

class JobRepository:
    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = db_path

    def connect(self):
        """Create database connection."""
        # Make sure the parent directory exists
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if needed
        from app.db.init_db import init_database
        init_database(str(db_path))
        
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn

    async def create(self, job: Job) -> bool:
        """Create a new job record if it doesn't exist."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            # Check if job already exists
            cursor.execute("SELECT id FROM jobs WHERE id = ?", (job.id,))
            if cursor.fetchone():
                return False  # Job already exists
            
            query = """
            INSERT INTO jobs (
                id, title, company, location, description,
                seniority_level, application_url, applied, scraped_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (
                job.id,
                job.title,
                job.company,
                job.location,
                job.description,
                job.seniority_level,
                job.application_url,
                job.applied,
                job.scraped_date
            )
            
            cursor.execute(query, values)
            conn.commit()
            return True
        finally:
            conn.close()
    
    async def get(self, job_id: str) -> Optional[Dict]:
        """Get job by ID."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    async def get_all(self) -> List[Dict]:
        """Get all jobs."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    async def update(self, job_id: str, data: Dict) -> bool:
        """Update job record."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            # Build update query dynamically based on provided fields
            set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
            query = f"UPDATE jobs SET {set_clause} WHERE id = ?"
            
            # Add job_id to the values
            values = list(data.values())
            values.append(job_id)
            
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    async def delete(self, job_id: str) -> bool:
        """Delete job record."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    async def mark_as_applied(self, job_id: str) -> bool:
        """Mark a job as applied."""
        return await self.update(job_id, {"applied": True})

    async def get_application_url(self, job_id: str) -> Optional[str]:
        """Get job's application URL."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT application_url FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return row['application_url'] if row else None
        finally:
            conn.close()
