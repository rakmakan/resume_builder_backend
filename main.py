#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import openai
from app.ai_resume_builder import AIResumeBuilder

async def main():
    # Load environment variables
    load_dotenv()
    
    # Check if OPENAI_API_KEY is set
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please make sure your .env file contains a valid API key.")
        return
        
    # Initialize the database directory and AI resume builder
    db_dir = Path(__file__).parent / 'database'
    db_dir.mkdir(exist_ok=True, mode=0o755)  # Set proper directory permissions
    db_path = str(db_dir / 'resume.sqlite')
    
    # Initialize database if it doesn't exist
    if not Path(db_path).exists():
        from app.db.init_db import init_database
        init_database(db_path)
        print(f"Initialized database at: {db_path}")
    
    builder = AIResumeBuilder(db_path)
    
    print("\nWelcome to AI Resume Builder!")
    
    # Read job description from file
    job_desc_path = Path(__file__).parent / 'test_data' / 'job_description.txt'
    try:
        with open(job_desc_path, 'r') as f:
            job_description = f.read()
        print(f"Successfully read job description from {job_desc_path}")
    except FileNotFoundError:
        print(f"Error: Could not find job description file at {job_desc_path}")
        return
    
    # Analyze job description
    print("\nAnalyzing job description...")
    company_id = await builder.analyze_job_description(job_description)
    
    # Read background from file
    background_path = Path(__file__).parent / 'test_data' / 'background.txt'
    try:
        with open(background_path, 'r') as f:
            my_background = f.read()
        print(f"Successfully read background from {background_path}")
    except FileNotFoundError:
        print(f"Error: Could not find background file at {background_path}")
        return
    
    # Create targeted resume
    print("\nCreating your targeted resume...")
    resume_id = await builder.create_resume(company_id, my_background)
    print(f"\nResume created successfully! Resume ID: {resume_id}")

if __name__ == "__main__":
    asyncio.run(main())
