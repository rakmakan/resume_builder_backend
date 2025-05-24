from pathlib import Path
from app.db.database import DatabaseInspector
from app.db.repository import ResumeRepository

def main():
    # Get the database path
    db_path = str(Path(__file__).parent.parent / 'database' / 'resume.sqlite')
    
    # First, let's inspect the database and create Pydantic models
    inspector = DatabaseInspector(db_path)
    
    # Get all tables
    print("Available tables:")
    tables = inspector.get_all_tables()
    print(tables)
    
    # Get schema for each table
    print("\nTable schemas:")
    for table in tables:
        print(f"\n{table}:")
        schema = inspector.get_table_schema(table)
        for column in schema:
            print(f"  {column['name']}: {column['type']}")
    
    # Create Pydantic models
    print("\nCreating Pydantic models...")
    models = inspector.get_all_models()
    for table_name, model in models.items():
        print(f"\n{table_name} model fields:")
        for field_name, field in model.model_fields.items():
            print(f"  {field_name}: {field.annotation}")
    
    # Example of using the repository to create a resume
    repo = ResumeRepository(db_path)
    
    # Create a new resume
    resume_id = repo.create_resume(
        name="Python Generated Resume",
        description="A resume created using the Python backend"
    )
    print(f"\nCreated resume with ID: {resume_id}")
    
    # Add personal information
    personal_info_id = repo.add_personal_info(
        resume_id=resume_id,
        name="John Doe",
        contact_info="john@example.com | (555) 123-4567 | github.com/johndoe"
    )
    print(f"Added personal info with ID: {personal_info_id}")
    
    # Add professional summary
    summary_id = repo.add_summary(
        resume_id=resume_id,
        content="Experienced software engineer with expertise in Python and web development."
    )
    print(f"Added summary with ID: {summary_id}")
    
    # Add education
    education_id = repo.add_education(
        resume_id=resume_id,
        data={
            "degree": "Bachelor of Science in Computer Science",
            "institution": "Tech University",
            "location": "Silicon Valley, CA",
            "date_range": "2018 - 2022",
            "description": "Graduated with honors"
        }
    )
    print(f"Added education with ID: {education_id}")
    
    # Add skill category and skills
    category_id = repo.add_skill_category(
        resume_id=resume_id,
        name="Programming Languages"
    )
    
    skill_id = repo.add_skill(
        resume_id=resume_id,
        category_id=category_id,
        data={
            "name": "Python",
            "proficiency": 90
        }
    )
    print(f"Added skill category with ID: {category_id} and skill with ID: {skill_id}")
    
    # Add work experience with accomplishments
    experience_id = repo.add_experience(
        resume_id=resume_id,
        data={
            "job_title": "Senior Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "date_range": "2022 - Present",
            "accomplishments": [
                "Led development of microservices architecture",
                "Improved system performance by 50%",
                "Mentored junior developers"
            ]
        }
    )
    print(f"Added experience with ID: {experience_id}")
    
    # Add a project
    project_id = repo.add_project(
        resume_id=resume_id,
        data={
            "title": "Resume Builder",
            "technologies": "Python, SQLite, Pydantic",
            "link": "https://github.com/johndoe/resume-builder",
            "description": "A full-stack resume builder application"
        }
    )
    print(f"Added project with ID: {project_id}")

if __name__ == "__main__":
    main()
