"""Configuration settings for the resume builder application."""
from pathlib import Path

# Database configuration
# Set the external database path
DATABASE_PATH = "/Users/rakshitmakan/Documents/resume_builder/database/resume.sqlite"
DATABASE_DIR = Path(DATABASE_PATH).parent
