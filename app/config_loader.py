"""
Centralized configuration loader for Resume Builder Backend
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    _app_config: Dict[str, Any] = None
    _db_config: Dict[str, Any] = None
    
    @classmethod
    def get_app_config(cls) -> Dict[str, Any]:
        """Load application configuration."""
        if cls._app_config is None:
            # Try Docker path first, then local path
            docker_path = Path('/config/app.json')
            local_path = Path(__file__).parent.parent.parent / 'config' / 'app.json'
            
            config_path = docker_path if docker_path.exists() else local_path
            
            if not config_path.exists():
                raise FileNotFoundError(f"App configuration file not found: {config_path}")
            
            with open(config_path, 'r') as f:
                cls._app_config = json.load(f)
        
        return cls._app_config
    
    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """Load database configuration."""
        if cls._db_config is None:
            # Try Docker path first, then local path
            docker_path = Path('/config/database.json')
            local_path = Path(__file__).parent.parent.parent / 'config' / 'database.json'
            
            config_path = docker_path if docker_path.exists() else local_path
            
            if not config_path.exists():
                raise FileNotFoundError(f"Database configuration file not found: {config_path}")
            
            with open(config_path, 'r') as f:
                cls._db_config = json.load(f)
        
        return cls._db_config
    
    @classmethod
    def get_database_path(cls) -> str:
        """Get database path."""
        # Check if running in Docker
        docker_db_path = '/app/database/resume.sqlite'
        if os.path.exists('/app/database'):
            return docker_db_path
        
        # Use config for local development
        db_config = cls.get_db_config()
        return db_config['database']['absolute_path']
    
    @classmethod
    def get_root_path(cls) -> str:
        """Get application root path."""
        app_config = cls.get_app_config()
        return app_config['paths']['root']
    
    @classmethod
    def get_path(cls, path_key: str) -> str:
        """Get specific path from configuration."""
        app_config = cls.get_app_config()
        return app_config['paths'].get(path_key)
    
    @classmethod
    def is_backup_enabled(cls) -> bool:
        """Check if backup is enabled."""
        db_config = cls.get_db_config()
        return db_config.get('backup', {}).get('enabled', False)
    
    @classmethod
    def get_backup_directory(cls) -> str:
        """Get backup directory."""
        db_config = cls.get_db_config()
        backup_dir = db_config.get('backup', {}).get('directory', '../database/backups')
        
        # Convert relative path to absolute
        if not os.path.isabs(backup_dir):
            backup_dir = os.path.join(cls.get_root_path(), backup_dir.lstrip('../'))
        
        return backup_dir