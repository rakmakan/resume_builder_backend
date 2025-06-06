from typing import Any, Dict, List, Optional
import sqlite3
from datetime import datetime

class ResumeRepository:
    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """Create database connection."""
        if not self.conn:
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

    def create_resume(self, name: str, job_id: str, description: Optional[str] = None) -> int:
        """Create a new resume and return its ID."""
        self.connect()
        try:
            query = """
            INSERT INTO resumes (name, job_id, description, created_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(query, (name, job_id, description))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_personal_info(self, resume_id: int, name: str, contact_info: str) -> int:
        """Add personal information for a resume."""
        self.connect()
        try:
            query = """
            INSERT INTO personal_info (resume_id, name, contact_info, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(query, (resume_id, name, contact_info))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_personal_info_detail(self, resume_id: int, detail_name: str, detail_icon: str, detail_info: str) -> int:
        """Add personal information detail for a resume."""
        self.connect()
        try:
            query = """
            INSERT INTO personal_info_details (
                resume_id, detail_name, detail_icon, detail_info, updated_at
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(query, (resume_id, detail_name, detail_icon, detail_info))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_summary(self, resume_id: int, content: str) -> int:
        """Add professional summary to a resume."""
        self.connect()
        try:
            query = """
            INSERT INTO summary (resume_id, content, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(query, (resume_id, content))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_education(self, resume_id: int, data: Dict[str, Any]) -> int:
        """Add education entry to a resume."""
        self.connect()
        try:
            query = """
            INSERT INTO education (
                resume_id, degree, institution, location, 
                date_range, description, is_visible, display_order, 
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            params = (
                resume_id,
                data['degree'],
                data['institution'],
                data.get('location'),
                data.get('date_range'),
                data.get('description'),
                data.get('is_visible', 1),
                data.get('display_order', 0)
            )
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_skill_category(self, resume_id: int, name: str, display_order: Optional[int] = None) -> int:
        """Add a skill category to a resume."""
        self.connect()
        try:
            query = """
            INSERT INTO skill_categories (
                resume_id, name, display_order, is_visible, updated_at
            ) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(query, (resume_id, name, display_order))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_skill(self, resume_id: int, category_id: int, data: Dict[str, Any]) -> int:
        """Add a skill to a category."""
        self.connect()
        try:
            query = """
            INSERT INTO skills (
                resume_id, category_id, name, proficiency,
                is_visible, display_order, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            params = (
                resume_id,
                category_id,
                data['name'],
                data.get('proficiency'),
                data.get('is_visible', 1),
                data.get('display_order', 0)
            )
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_experience(self, resume_id: int, data: Dict[str, Any]) -> int:
        """Add work experience to a resume."""
        self.connect()
        try:
            query = """
            INSERT INTO experience (
                resume_id, job_title, company, location,
                date_range, is_visible, display_order, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            params = (
                resume_id,
                data['job_title'],
                data['company'],
                data.get('location'),
                data.get('date_range'),
                data.get('is_visible', 1),
                data.get('display_order', 0)
            )
            self.cursor.execute(query, params)
            exp_id = self.cursor.lastrowid

            # Add accomplishments if provided
            if 'accomplishments' in data and data['accomplishments']:
                for idx, desc in enumerate(data['accomplishments']):
                    self.add_job_accomplishment(
                        resume_id=resume_id,
                        experience_id=exp_id,
                        description=desc,
                        display_order=idx
                    )

            self.conn.commit()
            return exp_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_job_accomplishment(self, resume_id: int, experience_id: int, 
                             description: str, display_order: Optional[int] = None) -> int:
        """Add a job accomplishment."""
        self.connect()
        try:
            query = """
            INSERT INTO job_accomplishments (
                resume_id, experience_id, description,
                display_order, is_visible, updated_at
            ) VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(query, (resume_id, experience_id, description, display_order))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_project(self, resume_id: int, data: Dict[str, Any]) -> int:
        """Add a project to a resume."""
        self.connect()
        try:
            query = """
            INSERT INTO projects (
                resume_id, title, technologies, link,
                description, is_visible, display_order, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            params = (
                resume_id,
                data['title'],
                data.get('technologies'),
                data.get('link'),
                data.get('description'),
                data.get('is_visible', 1),
                data.get('display_order', 0)
            )
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_resume_by_job_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get resume by job ID."""
        self.connect()
        try:
            query = """
            SELECT id, name, description, job_id, created_at, updated_at
            FROM resumes
            WHERE job_id = ?
            """
            self.cursor.execute(query, (job_id,))
            row = self.cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "job_id": row[3],
                    "created_at": row[4],
                    "updated_at": row[5]
                }
            return None
        except Exception as e:
            print(f"Error getting resume by job ID: {e}")
            return None
