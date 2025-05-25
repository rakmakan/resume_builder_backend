import sqlite3
from pathlib import Path

def init_database(db_path: str):
    """Initialize the SQLite database with all required tables."""
    # Ensure the parent directory exists with proper permissions
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create resumes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create company table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        about_business TEXT,
        qualifications TEXT,
        skills TEXT,
        job_description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create personal_info table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personal_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        contact_info TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id)
    )
    """)

    # Create summary table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id)
    )
    """)

    # Create education table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS education (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        degree TEXT NOT NULL,
        institution TEXT NOT NULL,
        location TEXT,
        date_range TEXT,
        description TEXT,
        is_visible INTEGER DEFAULT 1,
        display_order INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id)
    )
    """)

    # Create skill_categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skill_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        display_order INTEGER DEFAULT 0,
        is_visible INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id)
    )
    """)

    # Create skills table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        proficiency INTEGER,
        is_visible INTEGER DEFAULT 1,
        display_order INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id),
        FOREIGN KEY (category_id) REFERENCES skill_categories(id)
    )
    """)

    # Create experience table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experience (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        job_title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT,
        date_range TEXT,
        is_visible INTEGER DEFAULT 1,
        display_order INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id)
    )
    """)

    # Create job_accomplishments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_accomplishments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        experience_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        display_order INTEGER DEFAULT 0,
        is_visible INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id),
        FOREIGN KEY (experience_id) REFERENCES experience(id)
    )
    """)

    # Create projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        technologies TEXT,
        link TEXT,
        description TEXT,
        is_visible INTEGER DEFAULT 1,
        display_order INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id)
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    db_dir = Path(__file__).parent.parent / "database"
    db_dir.mkdir(exist_ok=True)
    db_path = str(db_dir / "resume.sqlite")
    init_database(db_path)
    print(f"Database initialized at: {db_path}")
