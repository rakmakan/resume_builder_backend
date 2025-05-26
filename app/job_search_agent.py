import os
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path
import asyncio
from .models import Job
from .db.job_repository import JobRepository
from openai import AsyncOpenAI
from .config import DATABASE_PATH

class JobSearchAgent:
    def __init__(self, api_key: str = None):
        """Initialize the Job Search Agent"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.client = AsyncOpenAI(api_key=self.api_key)

    def read_file_content(self, file_path: str) -> str:
        """Read content from a file"""
        with open(file_path, 'r') as f:
            return f.read()

    async def generate_search_queries(self, background_path: str, preferences_path: str) -> List[Dict]:
        """Generate optimized search queries based on background and preferences"""
        # Read background and preferences
        background = self.read_file_content(background_path)
        preferences = self.read_file_content(preferences_path)

        # Generate search queries using GPT-4
        prompt = f"""
        You are an expert job search assistant. Based on the candidate's background and preferences,
        generate 3 optimized LinkedIn job search queries to maximize relevant job matches.
        
        Important Guidelines:
        1. Keep keywords concise (2-4 key terms) to avoid over-filtering
        2. Use broader location (e.g., Canada instead of specific cities) unless preferences specify otherwise
        3. Include jobs from the past month to get more results
        4. Don't combine too many filters - prioritize the most important ones
        5. Use common industry terms that companies actually use in job postings

        Candidate's Background:
        {background}

        Job Search Preferences:
        {preferences}

        Format your response as a JSON array with 3 queries, each containing:
        - keywords: 2-4 main search terms that companies commonly use (e.g., "Data Scientist", "ML Engineer")
        - location: broader location (e.g., "Canada", "United States")
        - job_type: list of job types (e.g., ["Full-time", "Contract"])
        - experience_level: list of experience levels (e.g., ["Mid-Senior level", "Director"])
        - date_posted: time range (prefer "Past month" or "Past week" over "24 hours")
        - remote: boolean for remote preference
        - explanation: why this query is relevant

        Make each query focus on a different aspect of the candidate's experience, using different common job titles and skill combinations that employers search for.
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "system",
                    "content": "You are a job search expert who creates optimized search queries."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,
            )

            # Parse and validate the response
            queries = json.loads(response.choices[0].message.content)
            return queries

        except Exception as e:
            print(f"Error generating search queries: {e}")
            return []

    async def execute_job_search(self, queries: List[Dict], scraper) -> List[Job]:
        """Execute job searches using the generated queries"""
        all_jobs = []
        seen_job_ids = set()

        for query in queries:
            print(f"\nExecuting search query: {query['explanation']}")
            try:
                # Clean and format the query parameters
                keywords = ' '.join(query['keywords']) if isinstance(query['keywords'], list) else query['keywords']  # Handle both list and string
                location = query['location'].strip()
                job_type = query['job_type'] if isinstance(query['job_type'], list) else [query['job_type']]
                experience_level = query['experience_level'] if isinstance(query['experience_level'], list) else [query['experience_level']]
                
                jobs = scraper.search_jobs(
                    keywords=keywords,
                    location=location,
                    job_type=job_type,
                    experience_level=experience_level,
                    date_posted=query['date_posted'],
                    remote=query['remote'],
                    max_results=25
                )

                # Filter out duplicates
                for job in jobs:
                    if job['id'] not in seen_job_ids:
                        seen_job_ids.add(job['id'])
                        all_jobs.append(job)
                        
            except Exception as e:
                print(f"Error executing search query: {e}")
                continue

        return all_jobs

    async def save_jobs_to_database(self, jobs: List[Dict], job_repo: JobRepository) -> int:
        """Save unique jobs to the database"""
        saved_count = 0
        for job_data in jobs:
            job = Job(
                id=job_data["id"],
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                description=job_data["description"],
                seniority_level=job_data["seniority_level"],
                application_url=job_data["application_url"],
                applied=False,
                scraped_date=datetime.now()
            )
            
            if await job_repo.create(job):
                saved_count += 1
                print(f"Added new job: {job.title} at {job.company}")
            else:
                print(f"Job already exists: {job.title} at {job.company}")

        return saved_count

    def save_results_to_json(self, jobs: List[Dict], output_dir: str = "input") -> Optional[str]:
        """Save results to JSON file"""
        if not jobs:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"job_descriptions_{timestamp}.json"
        output_path = os.path.join(output_dir, filename)
        
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump({
                "jobs": [{
                    "id": job.get("id", str(i)),
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "description": job.get("description", ""),
                    "application_url": job.get("application_url", ""),
                    "seniority_level": job.get("seniority_level", ""),
                    "applied": job.get("applied", False),
                } for i, job in enumerate(jobs) if job.get("description")]
            }, f, indent=2)
        
        return output_path

async def main():
    from linkedin_job_description_scrapper import LinkedInJobScraper
    
    # Initialize components
    agent = JobSearchAgent()
    scraper = LinkedInJobScraper()
    job_repo = JobRepository(DATABASE_PATH)

    # File paths
    background_path = "test_data/background.txt"
    preferences_path = "test_data/job_search_preferences.txt"

    # Generate optimized search queries
    print("Generating optimized search queries based on background and preferences...")
    queries = await agent.generate_search_queries(background_path, preferences_path)

    if not queries:
        print("Failed to generate search queries")
        return

    # Execute job searches
    print("\nExecuting job searches...")
    all_jobs = await agent.execute_job_search(queries, scraper)

    if all_jobs:
        # Save results to JSON
        output_path = agent.save_results_to_json(all_jobs)
        if output_path:
            print(f"\nSaved job results to: {output_path}")

        # Save to database
        print("\nSaving jobs to database...")
        saved_count = await agent.save_jobs_to_database(all_jobs, job_repo)
        print(f"\nSuccessfully saved {saved_count} new jobs to database")
    else:
        print("No jobs found matching the search criteria")

if __name__ == "__main__":
    asyncio.run(main())
