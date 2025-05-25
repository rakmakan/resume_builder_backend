from typing import Dict, Optional
import sqlite3
from pathlib import Path
from app.models import Company

class CompanyRepository:
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

    async def create(self, company: Company) -> int:
        """Create a new company record."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            query = """
            INSERT INTO company (
                name, job_title, job_description, location,
                application_url, seniority_level, about,
                required_education, required_experience, required_skills
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (
                company.name,
                company.job_title,
                company.job_description,
                company.location,
                company.application_url,
                company.seniority_level,
                company.about,
                company.required_education,
                company.required_experience,
                company.required_skills
            )
            
            cursor.execute(query, values)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    async def get(self, company_id: int) -> Optional[Dict]:
        """Get company by ID."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM company WHERE id = ?", (company_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_company(self, company_id: int) -> Optional[Dict]:
        """Legacy method for compatibility. Use get() instead."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM company WHERE id = ?", (company_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    async def update(self, company_id: int, data: Dict) -> bool:
        """Update company record."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            # Build update query dynamically based on provided data
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            query = f"UPDATE company SET {set_clause} WHERE id = ?"
            
            # Add company_id to values
            values = list(data.values()) + [company_id]
            
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    async def delete(self, company_id: int) -> bool:
        """Delete company record."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM company WHERE id = ?", (company_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
