from pathlib import Path
from typing import Dict, List
import os
from dotenv import load_dotenv
from pydantic_ai import Agent

from app.db.company_repository import CompanyRepository
from app.db.repository import ResumeRepository
from app.models import (
    JobAnalysis, ParsedBackground, GeneratedSummary,
    GeneratedSkills, GeneratedExperience, GeneratedEducation,
    GeneratedProjects, Skill, SkillCategory, Experience,
    Education, Project, Company
)

# Load environment variables from .env file
load_dotenv()

class AIResumeBuilder:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.company_repo = CompanyRepository(db_path)
        self.resume_repo = ResumeRepository(db_path)
        
        # Initialize AI agents
        self.job_analyzer = Agent(
            'openai:gpt-4o-mini',
            output_type=JobAnalysis,
            system_prompt="""
            You are an expert job description analyzer. Extract key information from job descriptions.
            Your output MUST include ALL of these fields:
            - company_name: Name of the hiring company
            - about: Brief description of the company and role context
            - required_education: Educational qualifications, certifications, etc.
            - required_experience: Years of experience and specific domain expertise needed
            - required_skills: Both technical and soft skills needed for the role
            - job_description: The complete original job description text

            Important Rules:
            1. All fields are required - do not omit any field
            2. Keep the text in about/requirements fields concise but comprehensive
            3. Preserve all important details from the original description
            4. Use the exact field names as shown above
            5. For job_description, include the complete original text unchanged
            """
        )
        
        self.background_parser = Agent(
            'openai:gpt-4o-mini',
            output_type=ParsedBackground,
            system_prompt="""
            You are an expert resume parser. Extract structured information from a user's background text.
            Focus on organizing the information into clear categories:

            1. Personal Information:
               - Extract name and a professional headline
               - Organize contact details into structured format:
                 * Email (icon: fas fa-envelope)
                 * Phone (icon: fas fa-phone)
                 * LinkedIn (icon: fab fa-linkedin)
                 * GitHub (icon: fab fa-github)
                 * Portfolio/Website (icon: fas fa-globe)
               - Each contact detail should have:
                 * detail_name (e.g., "Email", "Phone")
                 * detail_icon (use Font Awesome icons as shown above)
                 * detail_info (the actual contact information)

            2. Education History:
               - Extract degree, institution, location, and dates
               - Keep descriptions concise (max 100 characters)
               - Split achievements into separate bullet points
               - Focus on measurable outcomes and technical relevance

            3. Work History:
               - Extract job titles, companies, locations, and dates
               - List key responsibilities as bullet points
               - Maintain specific details and metrics from the text

            4. Skills List:
               - Create a comprehensive list of technical and soft skills
               - Only include skills explicitly mentioned in the text

            5. Project History:
               - Extract project names, technologies used
               - Keep descriptions focused and technical
               - Maintain specific metrics and outcomes

            Important Rules:
            - Never add information not present in the input text
            - Preserve all numerical metrics and achievements
            - Keep language concise and specific
            - Split long descriptions into bullet points
            - For contact details, always include appropriate Font Awesome icons
            """
        )
        
        # Initialize section-specific agents
        self.summary_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedSummary,
            system_prompt="""
            You are an expert resume writer focusing on professional summaries.
            Create a compelling summary that:
            1. Aligns with the job requirements
            2. Highlights relevant experience and skills
            3. Shows clear value proposition
            4. Is concise and impactful (2-4 sentences)
            """
        )
        
        self.skills_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedSkills,
            system_prompt="""
            You are an expert in organizing and presenting professional skills.
            Organize skills into clear categories with proficiency levels that:
            1. Match skills required in the job description
            2. Include proficiency levels (0-100) for technical skills
            3. Group into logical categories (e.g., Programming Languages, Tools)
            4. Prioritize most relevant skills first
            """
        )
        
        self.experience_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedExperience,
            system_prompt="""
            You are an expert in crafting professional experience sections.
            For each position, create entries that:
            1. Highlight achievements relevant to the target role
            2. Use strong action verbs and metrics
            3. Demonstrate growth and impact
            4. Match the required experience in the job description

            Important ordering rules:
            1. Order experiences from most recent to oldest (reverse chronological order)
            2. Assign display_order starting from 0 for the most recent position
            3. Increment display_order by 1 for each older position
            4. Ensure all positions have a unique display_order value
            """
        )
        
        self.education_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedEducation,
            system_prompt="""
            You are an expert in presenting educational qualifications concisely.
            Important rules to follow:
            1. ONLY use information that exists in the provided background - do not invent or add details
            2. Keep descriptions short and focused (max 1-2 lines)
            3. Extract keywords from job requirements and use them to highlight relevant aspects of existing education
            4. Format achievements with metrics when available
            5. Focus on technical coursework and achievements that match the job requirements
            6. Do not add certifications or courses that aren't mentioned in the background
            """
        )
        
        self.projects_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedProjects,
            system_prompt="""
            You are an expert in showcasing professional projects. Follow these rules strictly:
            1. Description must be 100 characters or less
            2. Focus ONLY on projects using technologies from job requirements
            3. Format: "[Action] [Tech/Tool] to [Result] with [Metric]"
            4. Do not invent or add details not in original description
            5. Prioritize projects most relevant to job requirements
            6. Keep technical terms and metrics from original description
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

    async def analyze_job_description_with_company(self, company: Company) -> int:
        """
        Analyze a job description and save the analysis to the database.

        Args:
            company: Company object containing job details
            
        Returns:
            int: The company ID in the database
        """
        try:
            # Analyze the job description using OpenAI
            result = await self.job_analyzer.run({"job_description": company.job_description})
            
            # Update company with analysis results
            # Only update fields if they are returned in the analysis
            if hasattr(result.output, 'about'):
                company.about = result.output.about
            if hasattr(result.output, 'required_education'):
                company.required_education = result.output.required_education
            if hasattr(result.output, 'required_experience'):
                company.required_experience = result.output.required_experience
            if hasattr(result.output, 'required_skills'):
                company.required_skills = result.output.required_skills
            if hasattr(result.output, 'company_name') and not company.name:
                company.name = result.output.company_name
            
            # Save to database
            company_id = await self.company_repo.create(company)
            return company_id
            
        except Exception as e:
            print(f"Error analyzing job description: {str(e)}")
            raise

    async def create_resume(self, company_id: int, my_background: str) -> int:
        """Create a targeted resume based on job requirements."""
        # Get company information
        company_data = self.company_repo.get_company(company_id)
        if not company_data:
            raise ValueError("Company not found")

        # First, parse the background information
        parsed_background = await self.background_parser.run(my_background)
        background_info = parsed_background.output

        # Create resume in database
        resume_id = self.resume_repo.create_resume(
            name=f"Resume for {company_data['name']}",
            description=f"Targeted resume for position at {company_data['name']}"
        )            # Add basic personal information
        # Create a basic contact string from primary contact methods (email and phone)
        primary_contacts = [
            detail.detail_info 
            for detail in background_info.personal_info.contact_details
            if detail.detail_name in ['Email', 'Phone']
        ]
        contact_info = " | ".join(primary_contacts)
        
        self.resume_repo.add_personal_info(
            resume_id=resume_id,
            name=background_info.personal_info.name,
            contact_info=contact_info
        )
        
        # Add detailed contact information for UI display
        for detail in background_info.personal_info.contact_details:
            self.resume_repo.add_personal_info_detail(
                resume_id=resume_id,
                detail_name=detail.detail_name,
                detail_icon=detail.detail_icon,
                detail_info=detail.detail_info
            )

        # Generate and add summary
        summary_prompt = f"""
        Job Title: {company_data['job_title']}
        Job Description: {company_data['job_description']}
        Required Education: {company_data.get('required_education', '')}
        Required Experience: {company_data.get('required_experience', '')}
        Required Skills: {company_data.get('required_skills', '')}
        My Experience: {', '.join(exp.title for exp in background_info.work_history)}
        My Skills: {', '.join(background_info.skills_list)}
        """
        summary_result = await self.summary_generator.run(summary_prompt)
        self.resume_repo.add_summary(resume_id, summary_result.output.content)

        # Generate and add skills
        skills_prompt = f"""
        Required Skills: {company_data.get('required_skills', '')}
        My Skills: {', '.join(background_info.skills_list)}
        Role Requirements: {company_data['job_description']}
        """
        skills_result = await self.skills_generator.run(skills_prompt)
        for category in skills_result.output.categories:
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

        # Generate and add experience entries
        experience_prompt = f"""
        Job Title: {company_data['job_title']}
        Job Description: {company_data['job_description']}
        Required Experience: {company_data.get('required_experience', '')}
        Required Skills: {company_data.get('required_skills', '')}
        
        My Work History (already in reverse chronological order):
        {[{
            "title": exp.title,
            "company": exp.company,
            "date_range": exp.date_range,
            "location": exp.location,
            "responsibilities": exp.key_responsibilities
        } for exp in background_info.work_history]}
        
        Instructions:
        1. Keep the same chronological order as provided in the work history
        2. Assign display_order = 0 to the most recent position
        3. Increment display_order for each subsequent (older) position
        4. Ensure experiences are ordered exactly as in the original work history
        """
        experience_result = await self.experience_generator.run(experience_prompt)
        for exp in experience_result.output.experiences:
            exp_data = {
                "job_title": exp.job_title,
                "company": exp.company,
                "location": exp.location,
                "date_range": exp.date_range,
                "display_order": exp.display_order,  # Include the display_order
                "accomplishments": exp.accomplishments
            }
            self.resume_repo.add_experience(resume_id, exp_data)

        # Generate and add education entries
        education_prompt = f"""
        Job Title: {company_data['job_title']}
        Required Education: {company_data.get('required_education', '')}
        Required Skills: {company_data.get('required_skills', '')}

        Format each education entry based STRICTLY on this background information, do not add or invent details:
        {[{
            "degree": edu.degree,
            "institution": edu.institution,
            "date_range": edu.date_range,
            "location": edu.location,
            "description": edu.description
        } for edu in background_info.education_history]}

        Instructions:
        1. Use ONLY the information provided above
        2. Keep descriptions under 100 characters
        3. Focus on achievements and coursework that match job requirements
        4. Highlight technical aspects that align with required skills
        5. Include metrics and numbers when available
        6. Remove any generic or verbose language
        """
        education_result = await self.education_generator.run(education_prompt)
        for edu in education_result.output.education:
            edu_data = {
                "degree": edu.degree,
                "institution": edu.institution,
                "location": edu.location,
                "date_range": edu.date_range,
                "description": edu.description
            }
            self.resume_repo.add_education(resume_id, edu_data)

        # Generate and add project entries
        projects_prompt = f"""
        Job Title: {company_data['job_title']}
        Required Skills: {company_data.get('required_skills', '')}
        Job Requirements: {company_data['job_description']}

        Original Project Details:
        {[{
            "title": proj.title,
            "technologies": proj.technologies,
            "description": proj.description,
            "link": proj.link
        } for proj in background_info.project_history]}

        Instructions:
        1. Description Format: "[Action] [Tech/Tool] to [Result] with [Metric]"
        2. Keep descriptions under 100 characters
        3. Only mention technologies from job requirements
        4. Keep original metrics and outcomes
        5. Order projects by relevance to {company_data['name']}'s requirements
        6. Focus on technical implementation and measurable results
        """
        projects_result = await self.projects_generator.run(projects_prompt)
        for project in projects_result.output.projects:
            project_data = {
                "title": project.title,
                "technologies": project.technologies,
                "link": project.link,
                "description": project.description
            }
            self.resume_repo.add_project(resume_id, project_data)

        return resume_id
