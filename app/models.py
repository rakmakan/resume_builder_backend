from pydantic import BaseModel
from typing import List, Optional

class JobAnalysis(BaseModel):
    """Model for analyzed job description data"""
    company_name: str
    about_business: str
    qualifications: str
    skills: str
    job_description: str

class ResumeSection(BaseModel):
    """Model for resume sections"""
    content: str
    priority: float

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

class AIResumeContent(BaseModel):
    """Model for AI-generated resume content"""
    summary: str
    skills: List[SkillCategory]
    experience: List[Experience]
    education: List[Education]
    projects: List[Project]
