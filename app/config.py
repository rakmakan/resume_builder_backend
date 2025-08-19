"""Configuration settings for the resume builder application."""
from pathlib import Path
from .config_loader import ConfigLoader

# Database configuration using centralized config
DATABASE_PATH = ConfigLoader.get_database_path()
DATABASE_DIR = Path(DATABASE_PATH).parent
