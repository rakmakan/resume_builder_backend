from typing import Dict, Optional
import sqlite3
from pathlib import Path

class CompanyRepository:
    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """Create database connection."""
        if not self.conn:
            # Make sure the parent directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize database if needed
            from app.db.init_db import init_database
            init_database(self.db_path)
            
            # Connect to the database
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def create_table(self):
        """Create company table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS company (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            about_business TEXT,
            qualifications TEXT,
            skills TEXT,
            job_description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.cursor.execute(query)
        self.conn.commit()

    def add_company(self, data: Dict[str, str]) -> int:
        """Add a company and job description."""
        self.connect()
        try:
            query = """
            INSERT INTO company (
                name, about_business, qualifications, 
                skills, job_description
            ) VALUES (?, ?, ?, ?, ?)
            """
            params = (
                data['name'],
                data.get('about_business'),
                data.get('qualifications'),
                data.get('skills'),
                data['job_description']
            )
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_company(self, company_id: int) -> Optional[Dict]:
        """Get company information by ID."""
        self.connect()
        query = """
        SELECT name, about_business, qualifications, skills, job_description
        FROM company WHERE id = ?
        """
        self.cursor.execute(query, (company_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'name': row[0],
                'about_business': row[1],
                'qualifications': row[2],
                'skills': row[3],
                'job_description': row[4]
            }
        return None
