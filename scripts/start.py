#!/usr/bin/env python3
"""
SwissKnife AI Scraper Startup Script
"""

import asyncio
import sys
import os
import subprocess
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from utils.logging import setup_logging
from utils.port_manager import check_and_prepare_port


def check_ollama():
    """Check if Ollama is running"""
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        return response.status_code == 200
    except:
        return False


def start_ollama():
    """Start Ollama service"""
    print("🤖 Starting Ollama service...")
    try:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)  # Give it time to start
        return check_ollama()
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first.")
        print("   Visit: https://ollama.ai")
        return False


def check_models():
    """Check if required models are available"""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            models = result.stdout
            required_models = ["llama3.3", "mistral"]
            available_models = []
            
            for model in required_models:
                if model in models:
                    available_models.append(model)
            
            if not available_models:
                print("⚠️ No required models found. Installing default models...")
                install_default_models()
            else:
                print(f"✅ Found models: {', '.join(available_models)}")
            
            return True
    except:
        return False


def install_default_models():
    """Install default models"""
    default_models = ["mistral", "llama3.2"]  # Start with smaller models
    
    for model in default_models:
        print(f"📥 Installing {model}...")
        try:
            subprocess.run(["ollama", "pull", model], check=True)
            print(f"✅ {model} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {model}")


def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import crawl4ai
        import ollama
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False


def setup_environment():
    """Setup environment and directories"""
    settings = get_settings()
    
    # Create necessary directories
    directories = [
        settings.DATA_STORAGE_PATH,
        settings.CACHE_STORAGE_PATH,
        settings.LOG_STORAGE_PATH,
        settings.MODEL_STORAGE_PATH,
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Environment setup complete")


def main():
    """Main startup function"""
    print("🚀 Starting SwissKnife AI Scraper...")
    print("=" * 50)

    # Setup logging
    setup_logging()

    # Get settings early to access port
    settings = get_settings()

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Setup environment
    setup_environment()
    
    # Check Ollama
    if not check_ollama():
        print("⚠️ Ollama not running. Attempting to start...")
        if not start_ollama():
            print("❌ Failed to start Ollama. Please start it manually:")
            print("   ollama serve")
            sys.exit(1)
    else:
        print("✅ Ollama is running")
    
    # Check models
    check_models()

    # Check and prepare port
    print(f"🔌 Checking port {settings.PORT}...")
    if not check_and_prepare_port():
        print(f"❌ Failed to secure port {settings.PORT}")
        sys.exit(1)

    print("=" * 50)
    print("🎉 Startup checks complete!")
    print(f"🌐 Starting web server on port {settings.PORT}...")

    # Start the application
    settings = get_settings()
    
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG and settings.RELOAD_ON_CHANGE,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
