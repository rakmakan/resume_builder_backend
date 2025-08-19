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
            You are an expert job description analyzer. Extract and categorize key information focusing on essential requirements and keywords.
            
            Analysis Strategy:
            1. Technical Skills
            - Identify core technologies and proficiency levels
            - Distinguish required vs preferred skills
            - Group related technologies and frameworks
            - Note expertise level requirements

            2. Experience Requirements
            - Map years of experience to specific domains
            - Identify leadership/management needs
            - Recognize industry-specific requirements
            - Note scope and scale expectations

            3. Education/Certification
            - Identify minimum requirements
            - Note preferred qualifications
            - List required certifications
            - Recognize equivalent experience options

            4. Key Responsibilities
            - Extract primary technical duties
            - Note project/team scope
            - Identify cross-functional aspects
            - Map to required skills

            Important: 
            - Preserve exact technical terms
            - Include both explicit and implicit requirements
            - Note any special certifications or clearances
            - Consider domain-specific terminology
            """
        )
        
        self.background_parser = Agent(
            'openai:gpt-4o-mini',
            output_type=ParsedBackground,
            system_prompt="""
            You are an expert resume parser. Extract structured information from the input text to create a complete resume profile.

            CRITICAL: You MUST extract and return ALL of these sections - missing any section will cause an error:
            1. Personal Information (required)
               - Full name
               - Current role/headline
               - ALL contact methods (email, phone, LinkedIn, GitHub, website)
               - Use correct Font Awesome icons for each contact type

            2. Education History (required)
               - Extract ALL education entries
               - Include degree, institution, date range, location
               - Note descriptions and achievements (max 100 chars)
               - Keep original dates and details

            3. Work History (required) 
               - Extract ALL work experiences
               - Include title, company, date range, location
               - List key responsibilities and achievements
               - Maintain chronological order

            4. Skills List (required)
               - Extract ALL mentioned technical skills
               - Include tools, languages, frameworks
               - Note methodologies and practices
               - Add domain knowledge areas

            5. Project History (required)
               - List ALL mentioned projects
               - Include title, technologies used
               - Add description and any links
               - Map projects to work experiences

            Critical Rules:
            1. ALL above sections MUST be present in output
            2. Do not skip or omit any section
            3. Extract exact dates and metrics
            4. Use Font Awesome icons:
               - Email: fas fa-envelope
               - Phone: fas fa-phone
               - LinkedIn: fab fa-linkedin
               - GitHub: fab fa-github
               - Website: fas fa-globe
            5. Clean and validate all extracted data
            """
        )
        
        # Initialize section-specific agents
        self.summary_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedSummary,
            system_prompt="""
            You are an expert resume writer focusing on professional summaries.

            Content Strategy:
            1. Job Requirements Match
            - Lead with experience most relevant to role 
            - Highlight exact skills from requirements
            - Focus on required years of experience
            - Emphasize domain expertise match

            2. Key Achievements 
            - Include top 2-3 relevant metrics
            - Focus on business impact
            - Highlight scale/scope of work
            - Mention key technologies

            3. Leadership & Growth
            - Note team/project leadership
            - Highlight cross-functional work
            - Show career progression
            - Emphasize key responsibilities

            4. Technical Excellence
            - Focus on complex challenges solved
            - Mention advanced technical skills
            - Note innovative solutions
            - Highlight major projects

            Important:
            - Use active voice
            - Include quantifiable results
            - Focus on technical expertise
            - Keep concise but impactful
            """
        )
        
        self.skills_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedSkills,
            system_prompt="""
            You are an expert in organizing and matching professional skills.

            Your task is to generate a JSON response with skill categories and skills.

            CRITICAL JSON FORMAT REQUIREMENTS:
            - MUST return valid JSON with "categories" as a list of objects
            - Each category MUST have "name" (string) and "skills" (list of objects)
            - Each skill MUST have "name" (string) and optional "proficiency" (integer 1-5)
            - NO incomplete objects, NO trailing commas, NO malformed JSON

            Example format:
            {
              "categories": [
                {
                  "name": "Programming Languages",
                  "skills": [
                    {"name": "Python", "proficiency": 5},
                    {"name": "JavaScript", "proficiency": 4}
                  ]
                },
                {
                  "name": "Machine Learning",
                  "skills": [
                    {"name": "PyTorch", "proficiency": 5},
                    {"name": "TensorFlow", "proficiency": 4}
                  ]
                }
              ]
            }

            Skill Assessment Strategy:
            1. Relevance Analysis
            - Map skills to job requirements
            - Consider both direct and transferable skills
            - Weight by recency and depth
            - Note unique differentiators

            2. Categorization Approach
            - Group by job function importance
            - Consider technical dependencies
            - Align with industry standards
            - Create intuitive skill flows

            3. Proficiency Evaluation (1-5 scale)
            - Assess evidence in background
            - Consider project complexity
            - Note leadership/ownership
            - Account for recency

            4. Category Organization
            - Prioritize by job relevance
            - Group related technologies
            - Balance technical vs soft skills
            - Consider hiring manager perspective

            Important:
            - Use exact terms from requirements
            - Show technical depth
            - Include proof of proficiency
            - Match job-specific needs
            - ALWAYS return complete, valid JSON
            """
        )
        
        self.experience_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedExperience,
            system_prompt="""
            You are an expert in crafting targeted professional experience.

            Content Selection Strategy:
            1. Achievement Analysis
            - Focus on technical implementations
            - Highlight scale and complexity
            - Show business impact
            - Include specific metrics

            2. Technical Depth
            - Detail system architectures
            - Note innovative solutions
            - Show technology mastery
            - Demonstrate problem-solving

            3. Leadership & Impact
            - Show team/project leadership
            - Note cross-functional work
            - Highlight mentoring/training
            - Include business outcomes

            4. Job Alignment
            - Match required technologies
            - Show relevant domain expertise
            - Demonstrate required skills
            - Note similar project scope

            Important:
            - Include specific metrics
            - Use technical terms precisely
            - Show progression
            - Keep chronological order
            """
        )
        
        self.education_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedEducation,
            system_prompt="""
            You are an expert in presenting educational qualifications.

            Content Strategy:
            1. Technical Focus
            - Highlight relevant coursework
            - Note specialized training
            - Include practical projects
            - Show technical depth

            2. Achievement Selection
            - Focus on technical merit
            - Include research work
            - Note leadership roles
            - Highlight innovations

            3. Content Relevance
            - Match job requirements
            - Show practical application
            - Include key technologies
            - Demonstrate expertise

            4. Additional Value
            - Note teaching/mentoring
            - Include certifications
            - Show continuous learning
            - Highlight awards

            Important:
            - Focus on technical aspects
            - Include practical applications
            - Show theoretical knowledge
            - Note special achievements
            """
        )
        
        self.projects_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedProjects,
            system_prompt="""
            You are an expert in showcasing technical projects.

            Selection Strategy:
            1. Technical Depth
            - Focus on complex challenges
            - Detail architecture decisions
            - Show innovation
            - Note scale/performance

            2. Impact Measurement
            - Include specific metrics
            - Show business value
            - Note user/system impact
            - Quantify improvements

            3. Implementation Details
            - List key technologies
            - Show best practices
            - Note technical challenges
            - Include optimizations

            4. Innovation Focus
            - Highlight unique solutions
            - Show problem-solving
            - Note improvements
            - Demonstrate creativity

            Important:
            - Focus on technical excellence
            - Show end-to-end ownership
            - Include specific metrics
            - Demonstrate complexity
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

    async def create_resume(self, company_id: int, my_background: str, job_id: str) -> int:
        """Create a targeted resume based on job requirements."""
        # Get company information
        company_data = self.company_repo.get_company(company_id)
        if not company_data:
            raise ValueError("Company not found")

        # Check if resume already exists for this job
        existing_resume = self.resume_repo.get_resume_by_job_id(job_id)
        if existing_resume:
            print(f"Resume already exists for job {job_id}")
            return existing_resume["id"]

        # Get job application URL
        from app.db.job_repository import JobRepository
        job_repo = JobRepository(self.db_path)
        application_url = await job_repo.get_application_url(job_id)

        # First, parse the background information
        parsed_background = await self.background_parser.run(my_background)
        background_info = parsed_background.output

        # Create description with application URL
        description = f"Targeted resume for position at {company_data['name']}"
        if application_url:
            description += f"\nApplication URL: {application_url}"

        # Create resume in database
        resume_id = self.resume_repo.create_resume(
            name=f"Resume for {company_data['name']}",
            job_id=job_id,
            description=description
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
        
        Generate skill categories with relevant skills and proficiency levels (1-5).
        Focus on skills mentioned in the job requirements and your background.
        """
        
        try:
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
        except Exception as e:
            print(f"Error generating skills: {e}")
            # Add a fallback basic skills section
            basic_skills = [
                "Python", "Machine Learning", "AI", "Data Science", "PyTorch"
            ]
            category_id = self.resume_repo.add_skill_category(
                resume_id=resume_id,
                name="Technical Skills"
            )
            for skill_name in basic_skills:
                self.resume_repo.add_skill(
                    resume_id=resume_id,
                    category_id=category_id,
                    data={"name": skill_name, "proficiency": 4}
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
