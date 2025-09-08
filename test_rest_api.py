#!/usr/bin/env python3
"""Simple test script to verify REST API functionality."""

import asyncio
import json
import sys
from pathlib import Path

import requests
from requests.exceptions import ConnectionError, RequestException


def test_api_endpoint(base_url: str, endpoint: str, method: str = "GET", data: dict = None):
    """Test a single API endpoint."""
    url = f"{base_url}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"🔍 Testing {method} {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ Success: {result.get('message', 'OK')}")
                return True
            except json.JSONDecodeError:
                print(f"   ✅ Success (non-JSON response)")
                return True
        else:
            print(f"   ❌ Failed: {response.text[:100]}...")
            return False
            
    except ConnectionError:
        print(f"   ❌ Connection failed - is the server running?")
        return False
    except RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return False


def test_file_analysis_api(base_url: str):
    """Test file analysis endpoint with a real file."""
    # Find a Python file to test with
    test_file = None
    
    # Try to find a test file in the current project
    current_dir = Path(__file__).parent
    for py_file in current_dir.rglob("*.py"):
        if py_file.is_file() and py_file.stat().st_size < 10000:  # Small file
            test_file = str(py_file)
            break
    
    if not test_file:
        print("⚠️  No suitable test file found - skipping file analysis test")
        return False
    
    endpoint = "/api/v1/analysis/file"
    data = {
        "file_path": test_file,
        "include_metrics": True,
        "include_elements": True
    }
    
    print(f"🔍 Testing file analysis with: {test_file}")
    return test_api_endpoint(base_url, endpoint, "POST", data)


def main():
    """Run REST API tests."""
    base_url = "http://localhost:8000"
    
    print("🚀 Testing AST Viewer REST API")
    print(f"📡 Base URL: {base_url}")
    print("=" * 50)
    
    # Test endpoints
    tests = [
        # Health endpoints
        ("GET", "/", None),
        ("GET", "/health", None), 
        ("GET", "/metrics", None),
        ("GET", "/api/v1/health", None),
        ("GET", "/api/v1/info", None),
        
        # Visualization endpoints
        ("GET", "/api/v1/visualization/types", None),
        ("GET", "/api/v1/visualization/gallery", None),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, data in tests:
        if test_api_endpoint(base_url, endpoint, method, data):
            passed += 1
        print()
    
    # Test file analysis if possible
    if test_file_analysis_api(base_url):
        passed += 1
    total += 1
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed! REST API is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the server logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
