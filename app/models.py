from pydantic import BaseModel
from typing import List, Optional, Dict

class Skill(BaseModel):
    """Model for a single skill"""
    name: str
    proficiency: Optional[int] = None

class SkillCategory(BaseModel):
    """Model for a skill category with its skills"""
    name: str
    skills: List[Skill]

class Experience(BaseModel):
    """Model for work experience"""
    job_title: str
    company: str
    location: Optional[str] = None
    date_range: Optional[str] = None
    display_order: int  # Required field, no default value
    accomplishments: List[str] = []

class Education(BaseModel):
    """Model for education"""
    degree: str
    institution: str
    location: Optional[str] = None
    date_range: Optional[str] = None
    description: Optional[str] = None

class Project(BaseModel):
    """Model for projects"""
    title: str
    technologies: Optional[str] = None
    link: Optional[str] = None
    description: Optional[str] = None

class WorkHistoryItem(BaseModel):
    """Model for a work history item"""
    title: str
    company: str
    date_range: str
    location: Optional[str] = None
    key_responsibilities: List[str] = []

class PersonalInfoDetail(BaseModel):
    """Model for personal information details used in UI display"""
    detail_name: str  # e.g., 'Email', 'Phone', 'GitHub', 'LinkedIn'
    detail_icon: str  # e.g., 'fas fa-envelope', 'fas fa-phone'
    detail_info: str  # The actual contact information

class PersonalInfo(BaseModel):
    """Model for personal information"""
    name: str
    contact_info: Optional[str] = None  # Basic contact info (typically email and phone)
    contact_details: List[PersonalInfoDetail] = []  # Detailed contact info with icons for UI

class EducationHistoryItem(BaseModel):
    """Model for an education history item"""
    degree: str
    institution: str
    date_range: str
    location: Optional[str] = None
    description: Optional[str] = None  # Should be concise, max 100 chars
    achievements: Optional[List[str]] = None  # List of specific, measurable achievements

class ProjectHistoryItem(BaseModel):
    """Model for a project history item"""
    title: str
    technologies: Optional[str] = None
    description: Optional[str] = None
    link: Optional[str] = None

class Company(BaseModel):
    """Model for company and job details"""
    name: str
    job_title: str
    job_description: str
    location: Optional[str] = None
    application_url: Optional[str] = None
    seniority_level: Optional[str] = None
    about: Optional[str] = None
    required_education: Optional[str] = None
    required_experience: Optional[str] = None
    required_skills: Optional[str] = None

class ParsedBackground(BaseModel):
    """Model for parsed user background"""
    personal_info: PersonalInfo
    education_history: List[EducationHistoryItem]
    work_history: List[WorkHistoryItem]
    skills_list: List[str]
    project_history: List[ProjectHistoryItem]

class GeneratedSummary(BaseModel):
    """Model for AI-generated summary"""
    content: str

class GeneratedSkills(BaseModel):
    """Model for AI-generated skills"""
    categories: List[SkillCategory]

class GeneratedExperience(BaseModel):
    """Model for AI-generated experience"""
    experiences: List[Experience]

class GeneratedEducation(BaseModel):
    """Model for AI-generated education"""
    education: List[Education]

class GeneratedProjects(BaseModel):
    """Model for AI-generated projects"""
    projects: List[Project]

class JobAnalysis(BaseModel):
    """Model for analyzed job description data"""
    company_name: str = ""  # Name of the hiring company
    about: str = ""  # Brief description of the company and role
    required_education: str = ""  # Required qualifications and certifications
    required_experience: str = ""  # Required years and type of experience
    required_skills: str = ""  # Required technical and soft skills
    job_description: str  # Complete original job description text
