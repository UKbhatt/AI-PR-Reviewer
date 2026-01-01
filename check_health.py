#!/usr/bin/env python
"""
Health check and verification script for the Code Review Agent system.
Tests all components are working correctly.
"""

import sys
import subprocess
import time
import requests
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_status(message: str, status: str):
    """Print status message with color."""
    if status == "ok":
        print(f"{GREEN}✓{RESET} {message}")
    elif status == "error":
        print(f"{RED}✗{RESET} {message}")
    elif status == "warning":
        print(f"{YELLOW}⚠{RESET} {message}")
    else:
        print(f"  {message}")

def check_ollama():
    """Check if Ollama is running and llama3 model is available."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print_status("Ollama API endpoint", "error")
            return False
        
        tags = response.json().get("models", [])
        if not tags:
            print_status("No Ollama models available", "warning")
            return False
        
        model_names = [m.get("name", "") for m in tags]
        has_llama3 = any("llama3" in name for name in model_names)
        
        if has_llama3:
            print_status("Ollama with llama3 model", "ok")
            return True
        else:
            print_status("Ollama found but llama3 not installed", "warning")
            print(f"  Available models: {', '.join(model_names)}")
            return False
            
    except requests.ConnectionError:
        print_status("Ollama service (http://localhost:11434)", "error")
        print("  Run: ollama serve")
        return False
    except Exception as e:
        print_status(f"Ollama check failed: {e}", "error")
        return False

def check_redis():
    """Check if Redis is running."""
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            redis_ok = data.get("redis_connected", False)
            if redis_ok:
                print_status("Redis connection", "ok")
                return True
            else:
                print_status("Redis not connected", "error")
                return False
    except requests.ConnectionError:
        print_status("FastAPI backend (http://localhost:8000)", "error")
        print("  Run: cd backend && python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_status(f"Redis check failed: {e}", "error")
        return False

def check_celery():
    """Check if Celery worker is running."""
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            celery_active = data.get("celery_active", False)
            if celery_active:
                print_status("Celery worker", "ok")
                return True
            else:
                print_status("Celery worker not running", "warning")
                print("  Run: cd backend && python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis")
                return False
    except Exception as e:
        print_status(f"Celery check failed: {e}", "error")
        return False

def check_frontend():
    """Check if frontend is running."""
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print_status("React frontend (http://localhost:5173)", "ok")
            return True
        else:
            print_status("Frontend returned unexpected status", "warning")
            return False
    except requests.ConnectionError:
        print_status("React frontend (http://localhost:5173)", "error")
        print("  Run: npm run dev (in project root)")
        return False
    except Exception as e:
        print_status(f"Frontend check failed: {e}", "error")
        return False

def check_backend():
    """Check if backend is running."""
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print_status("FastAPI backend (http://localhost:8000)", "ok")
            return True
        else:
            print_status("Backend returned unexpected status", "warning")
            return False
    except requests.ConnectionError:
        print_status("FastAPI backend (http://localhost:8000)", "error")
        print("  Run: cd backend && python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_status(f"Backend check failed: {e}", "error")
        return False

def main():
    """Run all checks."""
    print(f"\n{BOLD}Code Review Agent - System Health Check{RESET}\n")
    
    results = {
        "Backend": check_backend(),
        "Redis": check_redis(),
        "Celery": check_celery(),
        "Ollama": check_ollama(),
        "Frontend": check_frontend(),
    }
    
    print(f"\n{BOLD}Summary:{RESET}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for component, status in results.items():
        status_text = "✓" if status else "✗"
        color = GREEN if status else RED
        print(f"{color}{status_text}{RESET} {component}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print(f"\n{GREEN}All systems operational!{RESET}")
        print("You can now use the system. Visit: http://localhost:5173")
        return 0
    elif passed == total - 1:
        print(f"\n{YELLOW}Most systems operational. Check warnings above.{RESET}")
        return 1
    else:
        print(f"\n{RED}Some systems are not running. See details above.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
