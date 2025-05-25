import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import math
import time
from urllib.parse import quote_plus
import os

class LinkedInJobScraper:
    def __init__(self):
        """Initialize the LinkedIn Job Scraper"""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        self.job_listings_api = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        self.job_details_api = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"
    
    def search_jobs(
        self,
        keywords: str,
        location: str = "",
        job_type: List[str] = None,
        experience_level: List[str] = None,
        date_posted: str = None,
        remote: bool = False,
        max_results: int = 25
    ) -> List[Dict]:
        """
        Search for jobs on LinkedIn with given filters
        
        Args:
            keywords (str): Job title or keywords
            location (str): Job location
            job_type (List[str]): List of job types (e.g., ["Full-time", "Contract"])
            experience_level (List[str]): List of experience levels
            date_posted (str): When the job was posted (e.g., "Past week")
            remote (bool): If True, search for remote jobs only
            max_results (int): Maximum number of job results to fetch
            
        Returns:
            List[Dict]: List of job listings with details
        """
        try:
            # Build query parameters
            params = {
                "keywords": quote_plus(keywords),
                "location": quote_plus(location) if location else "",
                "start": 0
            }

            # Add experience level filter
            if experience_level:
                exp_levels = []
                for level in experience_level:
                    if "entry" in level.lower():
                        exp_levels.append("2")
                    elif "associate" in level.lower():
                        exp_levels.append("3")
                    elif "mid-senior" in level.lower():
                        exp_levels.append("4")
                    elif "director" in level.lower():
                        exp_levels.append("5")
                if exp_levels:
                    params["f_E"] = ",".join(exp_levels)

            # Add job type filter
            if job_type:
                job_types = []
                for jtype in job_type:
                    if "full-time" in jtype.lower():
                        job_types.append("F")
                    elif "part-time" in jtype.lower():
                        job_types.append("P")
                    elif "contract" in jtype.lower():
                        job_types.append("C")
                    elif "temporary" in jtype.lower():
                        job_types.append("T")
                    elif "internship" in jtype.lower():
                        job_types.append("I")
                if job_types:
                    params["f_JT"] = ",".join(job_types)

            # Add date posted filter
            if date_posted:
                if "24 hours" in date_posted.lower():
                    params["f_TPR"] = "r86400"
                elif "week" in date_posted.lower():
                    params["f_TPR"] = "r604800"
                elif "month" in date_posted.lower():
                    params["f_TPR"] = "r2592000"

            # Add remote filter
            if remote:
                params["f_WT"] = "2"  # Remote jobs

            print(f"Searching for jobs with parameters: {params}")
            
            job_ids = []
            page = 0
            jobs_per_page = 25

            # Collect job IDs
            while len(job_ids) < max_results:
                params["start"] = page * jobs_per_page
                
                try:
                    response = requests.get(
                        self.job_listings_api,
                        params=params,
                        headers=self.headers
                    )
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    job_cards = soup.find_all("li")
                    
                    if not job_cards:
                        print("No more jobs found")
                        break
                    
                    for job_card in job_cards:
                        try:
                            job_id = job_card.find("div", {"class": "base-card"}).get('data-entity-urn').split(":")[-1]
                            job_ids.append(job_id)
                            if len(job_ids) >= max_results:
                                break
                        except (AttributeError, IndexError):
                            continue
                    
                    page += 1
                    time.sleep(1)  # Be nice to LinkedIn's servers
                    
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching job listings: {e}")
                    break

            print(f"Found {len(job_ids)} job IDs")
            
            # Get detailed information for each job
            jobs = []
            for job_id in job_ids:
                try:
                    job_info = self._get_job_details(job_id)
                    if job_info:
                        jobs.append(job_info)
                    time.sleep(1)  # Be nice to LinkedIn's servers
                except Exception as e:
                    print(f"Error getting details for job {job_id}: {e}")
                    continue

            return jobs
            
        except Exception as e:
            print(f"Error during job search: {e}")
            return []
    
    def _get_job_details(self, job_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific job
        
        Args:
            job_id (str): LinkedIn job ID
            
        Returns:
            Optional[Dict]: Job details if successful, None otherwise
        """
        try:
            response = requests.get(
                self.job_details_api.format(job_id),
                headers=self.headers
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract job details
            try:
                company = soup.find("div", {"class": "top-card-layout__card"}).find("a").find("img").get('alt')
            except:
                company = "Company name not found"
                
            try:
                title = soup.find("div", {"class": "top-card-layout__entity-info"}).find("a").text.strip()
            except:
                title = "Job title not found"
                
            try:
                location = soup.find("div", {"class": "topcard__flavor-row"}).text.strip()
            except:
                location = "Location not found"
                
            try:
                description = soup.find("div", {"class": "description__text"}).text.strip()
            except:
                description = "Description not found"
                
            try:
                level = soup.find("ul", {"class": "description__job-criteria-list"}).find("li").text.replace("Seniority level", "").strip()
            except:
                level = "Level not found"

            return {
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "seniority_level": level,
                "application_url": f"https://www.linkedin.com/jobs/view/{job_id}",
                "scraped_date": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching job details: {e}")
            return None
        except Exception as e:
            print(f"Error parsing job details: {e}")
            return None
    
    def save_results(self, jobs: List[Dict], output_dir: str = "input"):
        """
        Save job results to the input directory with timestamp
        
        Args:
            jobs (List[Dict]): List of job listings
            output_dir (str): Directory to save the file (defaults to 'input')
        """
        if not jobs:
            print("No jobs to save")
            return
            
        try:
            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_descriptions_{timestamp}.json"
            output_path = os.path.join(output_dir, filename)
            
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Save with proper formatting
            with open(output_path, "w") as f:
                json.dump({
                    "jobs": [{
                        "id": job.get("job_id", str(i)),
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "description": job.get("description", ""),
                        "application_url": job.get("application_url", ""),
                        "seniority_level": job.get("seniority_level", "")
                    } for i, job in enumerate(jobs) if job.get("description")]
                }, f, indent=2)
                
            print(f"Results saved to {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error saving results: {e}")
            return None

def main():
    # Example usage
    scraper = LinkedInJobScraper()
    
    jobs = scraper.search_jobs(
        keywords="Data Scientist",
        location="Canada",
        job_type=["Full-time"],
        experience_level=["Mid-Senior level", "Associate"],
        date_posted="Past week",
        remote=True,
        max_results=10
    )
    
    if jobs:
        scraper.save_results(jobs, "input")

if __name__ == "__main__":
    main()