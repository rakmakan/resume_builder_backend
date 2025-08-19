#!/usr/bin/env python3
"""
FastAPI Server Entry Point for AI Resume Builder
Run this file to start the REST API service
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# Check for required environment variables
def check_environment():
    """Check if required environment variables are set"""
    required_vars = ['OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment")
        print("Example .env file content:")
        print("OPENAI_API_KEY=your_openai_api_key_here")
        return False
    
    return True

def setup_database():
    """Initialize database if it doesn't exist"""
    try:
        from app.config import DATABASE_PATH
        from app.db.init_db import init_database
        
        # Create database directory if it doesn't exist
        Path(DATABASE_PATH).parent.mkdir(exist_ok=True, mode=0o755)
        
        # Initialize database if it doesn't exist
        if not Path(DATABASE_PATH).exists():
            init_database(DATABASE_PATH)
            print(f"✅ Initialized database at: {DATABASE_PATH}")
        else:
            print(f"✅ Database found at: {DATABASE_PATH}")
        
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def main():
    """Main entry point"""
    print("🚀 Starting AI Resume Builder API Server...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        sys.exit(1)
    
    # Import and run the FastAPI app
    try:
        import uvicorn
        from app.api_main import app
        
        print("✅ All checks passed!")
        print("📚 API Documentation: http://localhost:8001/docs")
        print("🔍 API Explorer: http://localhost:8001/redoc")
        print("❤️  Health Check: http://localhost:8001/api/health")
        print("\n🎯 Starting server on http://localhost:8001")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            reload=False,  # Disable reload in production
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ Failed to import required modules: {e}")
        print("Please install dependencies: pip install fastapi uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()