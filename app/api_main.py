#!/usr/bin/env python3
"""
FastAPI service for AI Resume Builder
Provides REST API endpoints for job management and resume generation
"""

import os
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from .config import DATABASE_PATH
from .ai_resume_builder import AIResumeBuilder
from .job_search_agent import JobSearchAgent
from .db.job_repository import JobRepository
from .db.company_repository import CompanyRepository
from .models import Job, Company

# Initialize FastAPI app
app = FastAPI(
    title="AI Resume Builder API",
    description="AI-powered resume builder with job scraping and analysis",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import shared models and functions from api_endpoints
from .api_endpoints import TASKS, APIResponse

# Additional models for main endpoints
class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# API Endpoints

@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information"""
    return APIResponse(
        success=True,
        message="AI Resume Builder API is running",
        data={
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/api/health"
        }
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        job_repo = JobRepository(DATABASE_PATH)
        await job_repo.get_all()
        
        # Test OpenAI API key
        openai_key = os.getenv('OPENAI_API_KEY')
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "openai_api": "configured" if openai_key else "missing",
            "services": {
                "job_repository": "operational",
                "ai_builder": "operational"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/api/config")
async def get_config():
    """Get current API configuration"""
    return {
        "database_path": DATABASE_PATH,
        "openai_configured": bool(os.getenv('OPENAI_API_KEY')),
        "supported_features": [
            "job_search",
            "resume_generation", 
            "background_analysis",
            "company_analysis"
        ]
    }

@app.get("/api/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of a background task"""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = TASKS[task_id]
    return TaskStatus(**task)

@app.get("/api/tasks", response_model=List[TaskStatus])
async def list_tasks():
    """List all tasks"""
    return [TaskStatus(**task) for task in TASKS.values()]

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a completed task"""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del TASKS[task_id]
    return APIResponse(success=True, message="Task deleted")

# Background task functions are now in api_endpoints.py

# Include API endpoints
from .api_endpoints import router
app.include_router(router)

if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run(
        "app.api_main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )