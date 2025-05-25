from pathlib import Path
from typing import Dict, List
import os
from dotenv import load_dotenv
from pydantic_ai import Agent

from app.db.company_repository import CompanyRepository
from app.db.repository import ResumeRepository
from app.models import JobAnalysis, AIResumeContent

# Load environment variables from .env file
load_dotenv()

class AIResumeBuilder:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.company_repo = CompanyRepository(db_path)
        self.resume_repo = ResumeRepository(db_path)
        
        # Initialize AI agents
        self.job_analyzer = Agent(
            'openai:gpt-4',
            output_type=JobAnalysis,
            system_prompt="""
            You are an expert job description analyzer. Extract key information from job descriptions.
            Focus on identifying:
            1. Company name
            2. About the business/company
            3. Required qualifications (education, certifications, years of experience)
            4. Required technical and soft skills
            Be concise but comprehensive in your analysis.
            """
        )
        
        self.resume_creator = Agent(
            'openai:gpt-4',
            output_type=AIResumeContent,
            system_prompt="""
            You are an expert resume writer. Create a targeted resume based on the job requirements.
            Focus on creating a resume that matches the exact structure required:

            1. Summary: Write a compelling summary that aligns with the job requirements.

            2. Skills: Organize into categories (e.g., "Programming Languages", "Frameworks", "Tools")
               Each category should have:
               - name: Category name
               - skills: List of skills, each with:
                 - name: Skill name
                 - proficiency: Number from 0-100 (optional)

            3. Experience: List each position with:
               - job_title: Title of the position
               - company: Company name
               - location: Location (optional)
               - date_range: Employment period (optional)
               - accomplishments: List of specific achievements

            4. Education: List each degree with:
               - degree: Name of the degree
               - institution: School name
               - location: Location (optional)
               - date_range: Study period (optional)
               - description: Additional details (optional)

            5. Projects: List relevant projects with:
               - title: Project name
               - technologies: Technologies used (optional)
               - link: Project link (optional)
               - description: Project details (optional)

            Be professional, specific, and highlight achievements with metrics when possible.
            """
        )

    async def analyze_job_description(self, job_description: str) -> int:
        """Analyze job description and store in database."""
        # Analyze job description using AI
        result = await self.job_analyzer.run(job_description)
        analysis = result.output
        
        # Store in database
        company_data = {
            'name': analysis.company_name,
            'about_business': analysis.about_business,
            'qualifications': analysis.qualifications,
            'skills': analysis.skills,
            'job_description': job_description
        }
        return self.company_repo.add_company(company_data)

    async def create_resume(self, company_id: int, my_background: str) -> int:
        """Create a targeted resume based on job requirements."""
        # Get company information
        company_data = self.company_repo.get_company(company_id)
        if not company_data:
            raise ValueError("Company not found")
        
        # Create prompt for resume creation
        prompt = f"""
        Job Description:
        {company_data['job_description']}
        
        Required Qualifications:
        {company_data['qualifications']}
        
        Required Skills:
        {company_data['skills']}
        
        My Background:
        {my_background}
        
        Create a targeted resume that highlights my relevant experience and skills for this position.
        """
        
        # Generate resume content
        result = await self.resume_creator.run(prompt)
        content = result.output
        
        # Create resume in database
        resume_id = self.resume_repo.create_resume(
            name=f"Resume for {company_data['name']}",
            description=f"Targeted resume for position at {company_data['name']}"
        )
        
        # Add summary
        self.resume_repo.add_summary(resume_id, content.summary)
        
        # Add skills
        for category in content.skills:
            category_id = self.resume_repo.add_skill_category(
                resume_id=resume_id,
                name=category.name
            )
            for skill in category.skills:
                self.resume_repo.add_skill(
                    resume_id=resume_id,
                    category_id=category_id,
                    data={"name": skill.name, "proficiency": skill.proficiency}
                )
        
        # Add experience
        for exp in content.experience:
            exp_data = {
                "job_title": exp.job_title,
                "company": exp.company,
                "location": exp.location,
                "date_range": exp.date_range,
                "accomplishments": exp.accomplishments
            }
            self.resume_repo.add_experience(resume_id, exp_data)
        
        # Add education
        for edu in content.education:
            edu_data = {
                "degree": edu.degree,
                "institution": edu.institution,
                "location": edu.location,
                "date_range": edu.date_range,
                "description": edu.description
            }
            self.resume_repo.add_education(resume_id, edu_data)
        
        # Add projects
        for project in content.projects:
            project_data = {
                "title": project.title,
                "technologies": project.technologies,
                "link": project.link,
                "description": project.description
            }
            self.resume_repo.add_project(resume_id, project_data)
        
        return resume_id
