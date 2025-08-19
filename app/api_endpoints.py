"""
API endpoints for Resume Builder FastAPI service
Contains all REST endpoints for job management, resume generation, and data management
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
import json
import uuid
from datetime import datetime
from pathlib import Path

from .config import DATABASE_PATH
from .ai_resume_builder import AIResumeBuilder
from .job_search_agent import JobSearchAgent
from .db.job_repository import JobRepository
from .db.company_repository import CompanyRepository
from .models import Job, Company

# Pydantic Models for API
class JobSearchRequest(BaseModel):
    search_terms: List[str] = Field(..., description="Job search keywords")
    location: str = Field("United States", description="Job location")
    experience_level: str = Field("entry_level", description="Experience level filter")
    max_results: int = Field(50, description="Maximum results to return")
    
class BackgroundUpdateRequest(BaseModel):
    content: str = Field(..., description="User background text")
    
class ResumeGenerationRequest(BaseModel):
    job_id: int = Field(..., description="Job ID to generate resume for")
    background_content: Optional[str] = Field(None, description="Custom background content")

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    task_id: Optional[str] = None

# Global task tracking
TASKS: Dict[str, Dict[str, Any]] = {}

# Helper functions
def create_task(task_type: str, description: str) -> str:
    """Create a new background task tracking entry"""
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "task_id": task_id,
        "type": task_type,
        "status": "pending",
        "progress": 0,
        "message": description,
        "result": None,
        "error": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    return task_id

def update_task(task_id: str, status: str = None, progress: int = None, 
                message: str = None, result: Any = None, error: str = None):
    """Update task status"""
    if task_id in TASKS:
        task = TASKS[task_id]
        if status:
            task["status"] = status
        if progress is not None:
            task["progress"] = progress
        if message:
            task["message"] = message
        if result is not None:
            task["result"] = result
        if error:
            task["error"] = error
        task["updated_at"] = datetime.now()

# Background task functions
async def background_job_search(task_id: str, search_request: JobSearchRequest):
    """Background job search task"""
    try:
        update_task(task_id, status="running", progress=10, message="Initializing job search")
        
        # Initialize job search agent
        agent = JobSearchAgent()
        update_task(task_id, progress=20, message="Generating search queries")
        
        # Get background content
        background_path = Path(__file__).parent.parent / 'test_data' / 'background.txt'
        if not background_path.exists():
            raise ValueError("Background file not found. Please upload background information first.")
        
        # Create preferences content from request
        preferences_content = f"""
Job Search Preferences:

Search Terms: {', '.join(search_request.search_terms)}
Location: {search_request.location}
Experience Level: {search_request.experience_level}
Maximum Results: {search_request.max_results}

Preferred Job Types: Full-time, Contract
Remote Work: Preferred but not required
Salary Range: Competitive
Industry Focus: Technology, Software Development
"""
        
        # Save preferences to temporary file
        preferences_path = Path(__file__).parent.parent / 'test_data' / 'job_search_preferences.txt'
        preferences_path.write_text(preferences_content)
        
        # Generate search queries
        queries = await agent.generate_search_queries(str(background_path), str(preferences_path))
        update_task(task_id, progress=40, message=f"Generated {len(queries)} search queries")
        
        # Execute search
        update_task(task_id, progress=50, message="Searching for jobs")
        results = await agent.search_jobs(
            queries=queries,
            location=search_request.location,
            experience_level=search_request.experience_level,
            max_results=search_request.max_results
        )
        
        update_task(task_id, progress=80, message="Saving results to database")
        
        # Save to database
        job_repo = JobRepository(DATABASE_PATH)
        saved_jobs = []
        for job_data in results:
            # Convert dictionary to Job object
            job = Job(
                id=job_data.get('id', str(len(saved_jobs))),
                title=job_data.get('title', ''),
                company=job_data.get('company', ''),
                location=job_data.get('location', ''),
                description=job_data.get('description', ''),
                seniority_level=job_data.get('seniority_level', ''),
                application_url=job_data.get('application_url', ''),
                applied=False,
                scraped_date=datetime.now()
            )
            created = await job_repo.create(job)
            if created:
                saved_jobs.append(job_data)
        
        update_task(
            task_id, 
            status="completed", 
            progress=100, 
            message=f"Successfully found and saved {len(saved_jobs)} jobs",
            result={
                "jobs_found": len(saved_jobs),
                "job_ids": [job["id"] for job in saved_jobs],
                "search_queries": queries
            }
        )
        
    except Exception as e:
        update_task(
            task_id, 
            status="failed", 
            progress=0, 
            message="Job search failed",
            error=str(e)
        )

async def background_resume_generation(task_id: str, request: ResumeGenerationRequest):
    """Background resume generation task"""
    try:
        update_task(task_id, status="running", progress=10, message="Starting resume generation")
        
        # Get job details
        job_repo = JobRepository(DATABASE_PATH)
        job = await job_repo.get(str(request.job_id))
        if not job:
            raise ValueError(f"Job {request.job_id} not found")
        
        update_task(task_id, progress=20, message=f"Processing job: {job['title']} at {job['company']}")
        
        # Initialize AI builder
        builder = AIResumeBuilder(DATABASE_PATH)
        
        # Get or use background
        background_content = request.background_content
        if not background_content:
            # Try to read from default background file
            background_path = Path(__file__).parent.parent / 'test_data' / 'background.txt'
            if background_path.exists():
                background_content = background_path.read_text()
            else:
                raise ValueError("No background content provided and no default background found")
        
        update_task(task_id, progress=40, message="Analyzing job requirements")
        
        # Create company entry and analyze job
        company_repo = CompanyRepository(DATABASE_PATH)
        company_obj = Company(
            name=job["company"],
            job_title=job["title"], 
            job_description=job["description"],
            location=job.get("location", ""),
            application_url=job.get("application_url", ""),
            seniority_level=job.get("seniority_level", "")
        )
        company_id = await company_repo.create(company_obj)
        
        update_task(task_id, progress=60, message="Generating targeted resume")
        
        # Generate resume
        resume_id = await builder.create_resume(company_id, background_content, job["id"])
        
        update_task(
            task_id,
            status="completed",
            progress=100,
            message="Resume generated successfully",
            result={
                "resume_id": resume_id,
                "job_id": request.job_id,
                "company_id": company_id
            }
        )
        
    except Exception as e:
        update_task(
            task_id,
            status="failed", 
            progress=0,
            message="Resume generation failed",
            error=str(e)
        )

# Dependency injection
async def get_database_path():
    """Get database path from config"""
    return DATABASE_PATH

async def get_ai_builder():
    """Get AIResumeBuilder instance"""
    return AIResumeBuilder(DATABASE_PATH)

async def get_job_repository():
    """Get JobRepository instance"""
    return JobRepository(DATABASE_PATH)

async def get_company_repository():
    """Get CompanyRepository instance"""
    return CompanyRepository(DATABASE_PATH)

# Create API router
router = APIRouter(prefix="/api", tags=["resume_builder"])

# ============= JOB MANAGEMENT ENDPOINTS =============

@router.post("/jobs/search", response_model=APIResponse)
async def search_jobs(
    search_request: JobSearchRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a background job search task
    Returns a task ID to track progress
    """
    task_id = create_task("job_search", f"Searching for jobs: {', '.join(search_request.search_terms)}")
    
    # Start background task
    background_tasks.add_task(background_job_search, task_id, search_request)
    
    return APIResponse(
        success=True,
        message="Job search started",
        task_id=task_id
    )

@router.get("/jobs", response_model=APIResponse)
async def get_all_jobs(
    limit: int = 50,
    offset: int = 0,
    company: Optional[str] = None,
    job_repo = Depends(get_job_repository)
):
    """Get all jobs with optional filtering"""
    try:
        jobs = await job_repo.get_all()
        
        # Apply filters
        if company:
            jobs = [job for job in jobs if company.lower() in job.get("company", "").lower()]
        
        # Apply pagination
        total = len(jobs)
        jobs = jobs[offset:offset + limit]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(jobs)} jobs",
            data={
                "jobs": jobs,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}", response_model=APIResponse)
async def get_job(job_id: int, job_repo = Depends(get_job_repository)):
    """Get a specific job by ID"""
    try:
        job = await job_repo.get(str(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return APIResponse(
            success=True,
            message="Job retrieved",
            data={"job": job}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/jobs/{job_id}/apply", response_model=APIResponse)
async def mark_job_applied(job_id: int, job_repo = Depends(get_job_repository)):
    """Mark a job as applied"""
    try:
        job = await job_repo.get(str(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update job status (assuming we add this field)
        updated_job = await job_repo.update(job_id, {"applied": True, "applied_at": "now"})
        
        return APIResponse(
            success=True,
            message="Job marked as applied",
            data={"job": updated_job}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}", response_model=APIResponse)
async def delete_job(job_id: int, job_repo = Depends(get_job_repository)):
    """Delete a job"""
    try:
        job = await job_repo.get(str(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        await job_repo.delete(job_id)
        
        return APIResponse(
            success=True,
            message="Job deleted"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= RESUME GENERATION ENDPOINTS =============

@router.post("/resumes", response_model=APIResponse)
async def create_resume(
    request: ResumeGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a targeted resume for a specific job
    Returns a task ID to track progress
    """
    task_id = create_task("resume_generation", f"Generating resume for job {request.job_id}")
    
    # Start background task
    background_tasks.add_task(background_resume_generation, task_id, request)
    
    return APIResponse(
        success=True,
        message="Resume generation started",
        task_id=task_id
    )

@router.get("/resumes", response_model=APIResponse)
async def get_all_resumes(ai_builder = Depends(get_ai_builder)):
    """Get all generated resumes"""
    try:
        # This would need to be implemented in the AIResumeBuilder
        resumes = await ai_builder.get_all_resumes()
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(resumes)} resumes",
            data={"resumes": resumes}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resumes/{resume_id}", response_model=APIResponse)
async def get_resume(resume_id: int, ai_builder = Depends(get_ai_builder)):
    """Get a specific resume by ID"""
    try:
        resume = await ai_builder.get_resume_by_id(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return APIResponse(
            success=True,
            message="Resume retrieved",
            data={"resume": resume}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/resumes/{resume_id}", response_model=APIResponse)
async def delete_resume(resume_id: int, ai_builder = Depends(get_ai_builder)):
    """Delete a resume"""
    try:
        await ai_builder.delete_resume(resume_id)
        
        return APIResponse(
            success=True,
            message="Resume deleted"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= BACKGROUND MANAGEMENT ENDPOINTS =============

@router.post("/background", response_model=APIResponse)
async def update_background(request: BackgroundUpdateRequest):
    """Update user background information"""
    try:
        # Save background to file
        background_path = Path(__file__).parent.parent / 'test_data' / 'background.txt'
        background_path.parent.mkdir(exist_ok=True)
        background_path.write_text(request.content)
        
        return APIResponse(
            success=True,
            message="Background updated successfully",
            data={"content_length": len(request.content)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/background/upload")
async def upload_background_file(file: UploadFile = File(...)):
    """Upload background information from file"""
    try:
        if file.content_type not in ["text/plain", "application/octet-stream"]:
            raise HTTPException(status_code=400, detail="Only text files are supported")
        
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Save to background file
        background_path = Path(__file__).parent.parent / 'test_data' / 'background.txt'
        background_path.parent.mkdir(exist_ok=True)
        background_path.write_text(text_content)
        
        return APIResponse(
            success=True,
            message="Background file uploaded successfully",
            data={
                "filename": file.filename,
                "content_length": len(text_content)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/background", response_model=APIResponse)
async def get_background():
    """Get current background information"""
    try:
        background_path = Path(__file__).parent.parent / 'test_data' / 'background.txt'
        
        if not background_path.exists():
            return APIResponse(
                success=True,
                message="No background found",
                data={"content": "", "has_background": False}
            )
        
        content = background_path.read_text()
        
        return APIResponse(
            success=True,
            message="Background retrieved",
            data={
                "content": content,
                "has_background": True,
                "content_length": len(content)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/background/parse", response_model=APIResponse)
async def parse_background(
    request: BackgroundUpdateRequest,
    ai_builder = Depends(get_ai_builder)
):
    """Parse background information using AI"""
    try:
        # Use AI to parse the background
        parsed_data = await ai_builder.parse_background(request.content)
        
        return APIResponse(
            success=True,
            message="Background parsed successfully",
            data={"parsed_background": parsed_data}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= COMPANY ANALYSIS ENDPOINTS =============

@router.post("/analysis/job", response_model=APIResponse)
async def analyze_job(
    job_id: int,
    company_repo = Depends(get_company_repository),
    job_repo = Depends(get_job_repository),
    ai_builder = Depends(get_ai_builder)
):
    """Analyze a job description"""
    try:
        job = await job_repo.get(str(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Analyze job using AI
        analysis = await ai_builder.analyze_job_description(job["description"])
        
        # Save analysis to company repository
        company_obj = Company(
            name=job["company"],
            job_title=job["title"],
            job_description=job["description"],
            location=job.get("location", ""),
            application_url=job.get("application_url", ""),
            seniority_level=job.get("seniority_level", "")
        )
        
        company_id = await company_repo.create(company_obj)
        
        return APIResponse(
            success=True,
            message="Job analysis completed",
            data={
                "analysis": analysis,
                "company_id": company_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{company_id}", response_model=APIResponse)
async def get_analysis(company_id: int, company_repo = Depends(get_company_repository)):
    """Get company analysis results"""
    try:
        company = await company_repo.get(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company analysis not found")
        
        return APIResponse(
            success=True,
            message="Analysis retrieved",
            data={"company": company}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= UTILITY ENDPOINTS =============

@router.post("/config/test", response_model=APIResponse)
async def test_configuration():
    """Test API configuration and external services"""
    try:
        import os
        from openai import OpenAI
        
        results = {
            "database": False,
            "openai": False,
            "linkedin_scraper": False
        }
        
        # Test database
        try:
            job_repo = JobRepository(DATABASE_PATH)
            await job_repo.get_all()
            results["database"] = True
        except:
            pass
        
        # Test OpenAI
        try:
            if os.getenv('OPENAI_API_KEY'):
                client = OpenAI()
                # Simple test request
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                results["openai"] = True
        except:
            pass
        
        # Test LinkedIn scraper (basic import test)
        try:
            from .linkedin_job_description_scrapper import LinkedInJobScraper
            results["linkedin_scraper"] = True
        except:
            pass
        
        all_healthy = all(results.values())
        
        return APIResponse(
            success=all_healthy,
            message="Configuration test completed",
            data={
                "results": results,
                "overall_status": "healthy" if all_healthy else "issues_detected"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=APIResponse)
async def get_statistics(
    job_repo = Depends(get_job_repository),
    company_repo = Depends(get_company_repository)
):
    """Get API usage statistics"""
    try:
        jobs = await job_repo.get_all()
        companies = await company_repo.get_all()
        
        stats = {
            "total_jobs": len(jobs),
            "total_companies": len(companies),
            "total_resumes": 0,  # Would need to implement
            "recent_activity": {
                "jobs_added_today": 0,  # Would need date filtering
                "resumes_generated_today": 0
            }
        }
        
        return APIResponse(
            success=True,
            message="Statistics retrieved",
            data=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))