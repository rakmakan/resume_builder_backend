#!/usr/bin/env python3
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import openai
from app.ai_resume_builder import AIResumeBuilder
from app.config import DATABASE_PATH
from app.models import Company, Job
from app.db.job_repository import JobRepository

def get_latest_jobs_file(input_dir: str = "input") -> Path:
    """Get the most recent job descriptions file from the input directory."""
    job_files = list(Path(input_dir).glob("job_descriptions_*.json"))
    if not job_files:
        return Path(input_dir) / "job_descriptions.json"
    return max(job_files, key=lambda x: x.stat().st_mtime)

async def main():
    # Load environment variables
    load_dotenv()
    
    # Check if OPENAI_API_KEY is set
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please make sure your .env file contains a valid API key.")
        return
        
    # Get database path from config
    db_path = DATABASE_PATH
    
    # Create database directory if it doesn't exist
    Path(db_path).parent.mkdir(exist_ok=True, mode=0o755)
    
    # Initialize database if it doesn't exist
    if not Path(db_path).exists():
        from app.db.init_db import init_database
        init_database(db_path)
        print(f"Initialized database at: {db_path}")
    
    builder = AIResumeBuilder(db_path)
    job_repo = JobRepository(db_path)
    
    print("\nWelcome to AI Resume Builder!")
    
    # First check for existing jobs in database
    existing_jobs = await job_repo.get_all()
    if existing_jobs:
        print("\nFound existing jobs in database:")
        jobs_data = {'jobs': existing_jobs}
        for job in existing_jobs:
            print(f"- {job['title']} at {job['company']}")
        use_existing = input("\nWould you like to use existing jobs? (y/n): ").lower().strip()
        if use_existing == 'y':
            print("\nUsing existing jobs from database...")
        else:
            print("\nReading jobs from file...")
            # Read job descriptions from the latest JSON file
            jobs_file = get_latest_jobs_file()
            try:
                with open(jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                print(f"Successfully read job descriptions from {jobs_file}")
            except FileNotFoundError:
                print(f"Error: Could not find job descriptions file at {jobs_file}")
                return
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON format in {jobs_file}")
                return
    else:
        print("\nNo existing jobs found in database. Reading from file...")
        # Read job descriptions from the latest JSON file
        jobs_file = get_latest_jobs_file()
        try:
            with open(jobs_file, 'r') as f:
                jobs_data = json.load(f)
            print(f"Successfully read job descriptions from {jobs_file}")
        except FileNotFoundError:
            print(f"Error: Could not find job descriptions file at {jobs_file}")
            return
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {jobs_file}")
            return

    # Read background from file
    background_path = Path(__file__).parent / 'test_data' / 'background.txt'
    try:
        with open(background_path, 'r') as f:
            my_background = f.read()
        print(f"Successfully read background from {background_path}")
    except FileNotFoundError:
        print(f"Error: Could not find background file at {background_path}")
        return

    # Process each job description
    resume_ids = []
    for job_data in jobs_data['jobs']:
        # Skip incomplete job entries or non-mid-senior level positions
        if not all(key in job_data for key in ['id', 'title', 'company', 'description']):
            print("Skipping incomplete job entry")
            continue
            
        # Skip if not a mid-senior level position
        seniority_level = job_data.get('seniority_level', '').strip()
        if seniority_level != "Mid-Senior level":
            print(f"Skipping {job_data['title']} at {job_data['company']} - not a mid-senior level position ({seniority_level})")
            continue

        # Create Job model
        job = Job(
            id=job_data['id'],
            title=job_data['title'],
            company=job_data['company'],
            location=job_data.get('location', ''),
            description=job_data['description'],
            seniority_level=job_data.get('seniority_level', ''),
            application_url=job_data.get('application_url', ''),
            applied=False,
            scraped_date=datetime.now()
        )

        # Store job in database if it doesn't exist
        job_added = await job_repo.create(job)
        if job_added:
            print(f"\nAdded new job: {job.title} at {job.company}")
        else:
            print(f"\nJob already exists: {job.title} at {job.company}")
            
        # Create company with job details including application URL
        company = Company(
            name=job.company,
            job_title=job.title,
            job_description=job.description,
            location=job.location,
            application_url=job.application_url,
            seniority_level=job.seniority_level
        )
        company_id = await builder.analyze_job_description_with_company(company)
        
        print(f"Creating targeted resume for job {job.id}...")
        resume_id = await builder.create_resume(company_id, my_background, job.id)
        resume_ids.append({
            "job_id": job.id,
            "resume_id": resume_id,
            "company": job.company,
            "title": job.title,
            "application_url": job.application_url
        })
        print(f"Resume created successfully for job {job.id}! Resume ID: {resume_id}")

    print("\nAll resumes created successfully!")
    print("\nResume Details:")
    for resume in resume_ids:
        print(f"Job {resume['job_id']} at {resume['company']}")
        print(f"Position: {resume['title']}")
        print(f"Resume ID: {resume['resume_id']}")
        print(f"Application URL: {resume['application_url']}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
