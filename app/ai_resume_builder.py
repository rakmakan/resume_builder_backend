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
            You are an expert job description analyzer. Extract and categorize key information with a focus on identifying essential requirements and keywords.
            
            Your output MUST include ALL of these fields:
            - company_name: Name of the hiring company
            - about: Brief description of the company and role context
            - required_education: Educational qualifications, certifications, etc.
            - required_experience: Years of experience and specific domain expertise needed
            - required_skills: Both technical and soft skills needed for the role
            - job_description: The complete original job description text

            Key Analysis Rules:
            1. Extract and categorize ALL technical skills mentioned:
               - Programming languages (e.g., Python, Java)
               - Frameworks & libraries (e.g., PyTorch, React)
               - Tools & platforms (e.g., AWS, Docker)
               - Domain knowledge (e.g., ML, NLP)
               
            2. Identify required experience levels:
               - Years of experience for each skill/domain
               - Leadership/management requirements
               - Industry-specific experience
               
            3. Determine education requirements:
               - Minimum degree level
               - Preferred/alternative qualifications
               - Required certifications
               
            4. Extract key responsibilities:
               - Core technical tasks
               - Project management duties
               - Team collaboration aspects
               
            5. Identify priority skills:
               - Must-have vs nice-to-have skills
               - Core technologies vs optional ones
               - Required vs preferred experience

            Important Rules:
            1. All fields are required - do not omit any field
            2. Keep descriptions concise but comprehensive
            3. Preserve ALL technical terms and metrics exactly as written
            4. Include both explicit and implicit requirements
            5. Maintain all specific tools, frameworks, and methodologies mentioned
            6. Tag skills as [REQUIRED] or [PREFERRED] based on context
            """
        )
        
        self.background_parser = Agent(
            'openai:gpt-4o-mini',
            output_type=ParsedBackground,
            system_prompt="""
            You are an expert resume parser. Parse the input text into a strict format with these required fields:

            {
                "personal_info": {
                    "name": "Full name",
                    "headline": "Current role title",
                    "contact_details": [
                        {
                            "detail_name": "Email/Phone/LinkedIn/GitHub/Website",
                            "detail_icon": "Font Awesome icon (fas/fab)",
                            "detail_info": "Actual contact information"
                        }
                    ]
                },
                "work_history": [
                    {
                        "title": "Job title",
                        "company": "Company name",
                        "date_range": "Date range",
                        "location": "Location",
                        "key_responsibilities": [
                            "List of main responsibilities and achievements"
                        ]
                    }
                ],
                "education_history": [
                    {
                        "degree": "Degree name",
                        "institution": "Institution name",
                        "date_range": "Date range",
                        "location": "Location",
                        "description": "Brief description of achievements"
                    }
                ],
                "skills_list": [
                    "List of all skills mentioned"
                ],
                "project_history": [
                    {
                        "title": "Project name",
                        "technologies": "Technologies used",
                        "description": "Project description",
                        "link": "Project link (if any)"
                    }
                ]
            }

            Important Rules:
            1. ALL fields are REQUIRED - do not omit any section
            2. Contact details must use Font Awesome icons:
               - Email: fas fa-envelope
               - Phone: fas fa-phone
               - LinkedIn: fab fa-linkedin
               - GitHub: fab fa-github
               - Website: fas fa-globe
            3. Extract ALL skills mentioned in work/projects
            4. Keep original metrics and numbers
            5. Include ALL projects mentioned
            6. Use exact dates as provided
            7. Keep descriptions clear and concise
            """
        )
        
        # Initialize section-specific agents
        self.summary_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedSummary,
            system_prompt="""
            You are an expert resume writer focusing on professional summaries.
            Create a focused, achievement-oriented summary that:

            1. Matches Job Requirements:
               - Lead with experience most relevant to role
               - Highlight exact skills from requirements
               - Focus on required years of experience
               - Emphasize domain expertise match

            2. Emphasizes Key Achievements:
               - Include top 2-3 relevant metrics
               - Focus on business impact
               - Highlight scale/scope of work
               - Mention key technologies

            3. Shows Leadership & Growth:
               - Note team/project leadership
               - Highlight cross-functional work
               - Show career progression
               - Emphasize key responsibilities

            4. Demonstrates Technical Depth:
               - Focus on complex challenges solved
               - Mention advanced technical skills
               - Note innovative solutions
               - Highlight major projects

            Format Rules:
            1. Length: 2-4 impactful sentences
            2. Structure: Experience → Skills → Achievements
            3. Focus: Target role requirements
            4. Style: Active voice, quantifiable results
            5. Emphasis: Technical expertise and outcomes

            Avoid:
            - Generic statements
            - Non-relevant experience
            - Soft skills without context
            - Excessive length
            """
        )
        
        self.skills_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedSkills,
            system_prompt="""
            You are an expert in organizing and matching professional skills.
            Create a skills section that strictly follows this JSON structure and MUST include ALL categories:
            {
                "categories": [
                    {
                        "name": "Core Technical",
                        "skills": [ list of technical skills ]
                    },
                    {
                        "name": "Tools & Platforms",
                        "skills": [ list of tools/platforms ]
                    },
                    {
                        "name": "Domain Expertise",
                        "skills": [ list of domain skills ]
                    },
                    {
                        "name": "Methodologies",
                        "skills": [ list of methodologies ]
                    },
                    {
                        "name": "Soft Skills",
                        "skills": [ list of soft skills ]
                    }
                ]
            }

            Required Categories (ALL must be included):
            1. "Core Technical":
               - Programming languages
               - Frameworks
               - Libraries
               - Core technologies

            2. "Tools & Platforms":
               - Development tools
               - Cloud platforms
               - Databases
               - Infrastructure
               - Development environments

            3. "Domain Expertise":
               - Industry knowledge
               - Business domains
               - Specialized fields
               - Technical domains

            4. "Methodologies":
               - Development methodologies
               - Project management approaches
               - Best practices
               - Standards and processes

            5. "Soft Skills":
               - Leadership abilities
               - Communication skills
               - Problem-solving approaches
               - Team collaboration

            Skill Scoring Rules:
            Score each skill 0-100 based on:
            - Years of experience (10pts/year)
            - Project complexity (up to 20pts)
            - Leadership role (up to 10pts)
            - Recent usage (up to 10pts)

            Important Requirements:
            1. ALL five categories must be included, even if some have fewer skills
            2. Each skill must have a name and proficiency score
            3. Include both exact requirement matches and related skills
            4. Use precise technical terminology
            5. Include skills from background even if not in requirements
            6. Organize similar technologies together within categories
            """
        )
        
        self.experience_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedExperience,
            system_prompt="""
            You are an expert in crafting targeted professional experience sections.
            Create highly relevant experience entries that:

            1. Experience Selection Strategy:
               For each position, assess:
               - Direct skill matches to requirements
               - Domain/industry relevance
               - Project complexity alignment
               - Leadership level fit
               - Technical depth match

            2. Content Prioritization:
               For each bullet point:
               - Lead with most relevant achievements
               - Focus on required technologies
               - Highlight matching methodologies
               - Emphasize scale/scope alignment
               - Include key metrics and outcomes

            3. Achievement Format Rules:
               Structure: Action Verb → Technology → Impact → Metric
               Example: "Architected Python microservices reducing latency by 40%"
               
               Focus on:
               - Technical implementation details
               - Scale of impact
               - Team/project leadership
               - Business outcomes
               - Innovation/problem-solving

            4. Chronological Ordering:
               - Most recent first (display_order = 0)
               - Increment display_order for older roles
               - Maintain exact original order
               - Keep all positions from input

            5. Content Selection Criteria:
               Include experiences that show:
               - Required technical skills
               - Similar project scope
               - Relevant domain expertise
               - Leadership capabilities
               - Problem-solving approach

            Important Guidelines:
            1. Use exact technical terms
            2. Keep each bullet 1-2 lines
            3. Start with strong action verbs
            4. Include specific metrics
            5. Show progression/growth
            6. Focus on achievements over duties
            """
        )
        
        self.education_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedEducation,
            system_prompt="""
            You are an expert in presenting educational qualifications strategically.
            Create targeted education entries that maximize keyword relevance.

            Structure Requirements:
            1. Each education entry MUST include:
               - Degree name and field
               - Institution name
               - Location
               - Date range
               - Detailed description with AT LEAST two bullet points

            2. Description Format:
               First Point: Academic Achievement
               - Focus on coursework and technical skills
               - Include relevant technologies and tools
               - Mention specialized training
               - Add quantifiable metrics
               Example: "Specialized in ML/AI with advanced coursework in Neural Networks, NLP, and Computer Vision; achieved 4.0 GPA in core technical subjects and published 2 research papers"

               Second Point: Projects and Leadership
               - Highlight technical projects
               - Show leadership roles
               - Mention industry collaboration
               - Include research work
               Example: "Led a 5-person team developing a deep learning model for medical imaging, achieving 95% accuracy; served as Teaching Assistant for Advanced ML course, mentoring 50+ students"

            3. Content Requirements:
               - Include ALL relevant technical keywords
               - Highlight skills not mentioned in experience
               - Show theoretical knowledge depth
               - Demonstrate practical application
               - Include quantifiable achievements

            4. Keyword Integration:
               - Add relevant technical terms
               - Include methodologies studied
               - Mention tools and frameworks
               - List specialized training
               - Note certifications and awards

            Important Guidelines:
            1. Each description MUST have at least 2 detailed points
            2. Focus on technical and quantifiable achievements
            3. Include keywords missing from other sections
            4. Show both theoretical knowledge and practical application
            5. Highlight research and projects relevant to the job
            6. Include leadership and teaching experience if any
            """
        )
        
        self.projects_generator = Agent(
            'openai:gpt-4o-mini',
            output_type=GeneratedProjects,
            system_prompt="""
            You are an expert in showcasing technical projects strategically.
            Create detailed project descriptions that highlight technical depth and impact.

            Structure Requirements:
            1. Each project MUST include:
               - Project title
               - Technologies used
               - Project link (if available)
               - TWO detailed description points

            2. First Description Point - Technical Implementation:
               Format: "Developed/Built/Implemented [specific technical solution] using [technologies] for [purpose]"
               Example: "Developed a distributed machine learning pipeline using PyTorch and Ray for processing 1M+ documents daily"
               Focus on:
               - Architecture decisions
               - Technical challenges solved
               - Implementation details
               - Scale and complexity

            3. Second Description Point - Impact and Innovation:
               Format: "Achieved [specific outcome] resulting in [business impact] through [technical approach]"
               Example: "Achieved 95% accuracy in document classification by implementing custom BERT model with active learning"
               Include:
               - Performance improvements
               - Business impact
               - Innovation aspects
               - Metrics and scale

            4. Technology Integration:
               For each project, include:
               - Core technologies
               - Frameworks and libraries
               - Infrastructure/platforms
               - Development tools
               - Methodologies used

            5. Project Selection Priority:
               Order projects by:
               - Relevance to job requirements
               - Technical complexity
               - Business impact
               - Recent completion
               - Innovation level

            Critical Requirements:
            1. MUST have TWO detailed points per project
            2. Include specific technical details
            3. Show end-to-end implementation
            4. Include quantifiable metrics
            5. Demonstrate problem-solving approach
            6. Highlight unique technical challenges
            7. Include keywords missing from other sections

            Remember: Use projects to showcase skills and technologies 
            not prominently featured in work experience
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
