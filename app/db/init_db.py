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
        id INTEGER PRIMARY KEY,
        job_id TEXT,
        name TEXT NOT NULL,
        description TEXT,
        is_default INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )
    """)

    # Create company table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        job_title TEXT NOT NULL,
        job_description TEXT NOT NULL,
        location TEXT,
        application_url TEXT,
        seniority_level TEXT,
        about TEXT,
        required_education TEXT,
        required_experience TEXT,
        required_skills TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create personal_info table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personal_info (
        id INTEGER PRIMARY KEY,
        resume_id INTEGER,
        name TEXT NOT NULL,
        contact_info TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    )
    """)

    # Create personal_info_details table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personal_info_details (
        id INTEGER PRIMARY KEY,
        resume_id INTEGER,
        detail_name TEXT NOT NULL,
        detail_icon TEXT NOT NULL,
        detail_info TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    )
    """)

    # Create summary table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS summary (
        id INTEGER PRIMARY KEY,
        resume_id INTEGER,
        content TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    )
    """)

    # Create education table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS education (
        id INTEGER PRIMARY KEY,
        resume_id INTEGER,
        degree TEXT NOT NULL,
        institution TEXT NOT NULL,
        location TEXT,
        date_range TEXT,
        description TEXT,
        is_visible INTEGER DEFAULT 1,
        display_order INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    )
    """)

    # Create skill_categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skill_categories (
        id INTEGER PRIMARY KEY,
        resume_id INTEGER,
        name TEXT NOT NULL,
        display_order INTEGER,
        is_visible INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    )
    """)

    # Create skills table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY,
        resume_id INTEGER,
        category_id INTEGER,
        name TEXT NOT NULL,
        proficiency INTEGER,
        is_visible INTEGER DEFAULT 1,
        display_order INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES skill_categories(id) ON DELETE CASCADE
    )
    """)

    # Create experience table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experience (
        id INTEGER PRIMARY KEY,
        resume_id INTEGER,
        job_title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT,
        date_range TEXT,
        is_visible INTEGER DEFAULT 1,
        display_order INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    )
    """)

    # Create job_accomplishments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_accomplishments (
        id INTEGER PRIMARY KEY,
        resume_id INTEGER,
        experience_id INTEGER,
        description TEXT NOT NULL,
        display_order INTEGER,
        is_visible INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
        FOREIGN KEY (experience_id) REFERENCES experience(id) ON DELETE CASCADE
    )
    """)

    # Create projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        resume_id INTEGER,
        title TEXT NOT NULL,
        technologies TEXT,
        link TEXT,
        description TEXT,
        is_visible INTEGER DEFAULT 1,
        display_order INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    )
    """)

    # Create resume table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resume (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES company (id)
    )
    """)

    # Create jobs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT,
        description TEXT NOT NULL,
        seniority_level TEXT,
        application_url TEXT,
        applied INTEGER DEFAULT 0,
        scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    from app.config import DATABASE_PATH, DATABASE_DIR
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    init_database(DATABASE_PATH)
    print(f"Database initialized at: {DATABASE_PATH}")
