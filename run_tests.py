#!/usr/bin/env python3
"""
AST Viewer TDD Test Runner
==========================

This script provides convenient commands for running different types of tests
following Test-Driven Development (TDD) practices.

Usage:
    python run_tests.py [command] [options]

Commands:
    unit        - Run unit tests only (fast, no external dependencies)
    integration - Run integration tests (requires databases)
    neo4j       - Run Neo4j specific tests
    performance - Run performance tests
    all         - Run all tests
    tdd         - Run in TDD mode (watch for changes and re-run)
    coverage    - Run with coverage reporting
    
Examples:
    python run_tests.py unit
    python run_tests.py neo4j --verbose
    python run_tests.py coverage --html
    python run_tests.py tdd --watch src/
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, capture_output=False):
    """Run shell command and return result."""
    print(f"🔄 Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True)
        if result.returncode != 0:
            print(f"❌ Command failed with code {result.returncode}")
            if capture_output:
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking test dependencies...")
    
    required_packages = ["pytest", "pytest-cov", "pytest-asyncio"]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("💡 Install with: pip install -r tests/requirements-test.txt")
        return False
    
    print("✅ All test dependencies are installed")
    return True


def run_unit_tests(verbose=False):
    """Run unit tests only."""
    print("🧪 Running unit tests...")
    cmd = ["python", "-m", "pytest", "tests/", "-m", "unit"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_integration_tests(verbose=False):
    """Run integration tests."""
    print("🔗 Running integration tests...")
    print("⚠️  Note: Requires running databases (Neo4j, PostgreSQL, Redis)")
    
    cmd = ["python", "-m", "pytest", "tests/", "-m", "integration"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_neo4j_tests(verbose=False):
    """Run Neo4j specific tests."""
    print("📊 Running Neo4j tests...")
    cmd = ["python", "-m", "pytest", "tests/test_neo4j_tdd.py"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_performance_tests(verbose=False):
    """Run performance tests."""
    print("⚡ Running performance tests...")
    cmd = ["python", "-m", "pytest", "tests/", "-m", "performance", "--benchmark-only"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_all_tests(verbose=False):
    """Run all tests."""
    print("🎯 Running all tests...")
    cmd = ["python", "-m", "pytest", "tests/"]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_coverage_tests(html=False, verbose=False):
    """Run tests with coverage reporting."""
    print("📊 Running tests with coverage...")
    cmd = [
        "python", "-m", "pytest", "tests/",
        "--cov=src/ast_viewer",
        "--cov-report=term-missing"
    ]
    
    if html:
        cmd.extend(["--cov-report=html:tests/reports/coverage"])
        print("📄 HTML coverage report will be generated in tests/reports/coverage/")
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd)


def run_tdd_mode(watch_dir="src/", verbose=False):
    """Run in TDD mode with file watching."""
    print("👀 Running in TDD mode - watching for file changes...")
    print("💡 Install pytest-watch: pip install pytest-watch")
    
    cmd = [
        "ptw", 
        "--runner", "python -m pytest tests/test_neo4j_tdd.py",
        watch_dir
    ]
    
    if verbose:
        cmd.append("--verbose")
    
    # Check if pytest-watch is installed
    try:
        subprocess.run(["ptw", "--help"], capture_output=True)
    except FileNotFoundError:
        print("❌ pytest-watch not found. Install with: pip install pytest-watch")
        return False
    
    return run_command(cmd)


def setup_test_environment():
    """Set up test environment and directories."""
    print("🏗️  Setting up test environment...")
    
    # Create test directories
    test_dirs = [
        "tests/reports",
        "tests/reports/coverage", 
        "tests/reports/performance",
        "tests/fixtures",
        "tests/integration",
        "tests/unit"
    ]
    
    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {dir_path}")
    
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["PYTHONPATH"] = str(Path.cwd() / "src")
    
    print("✅ Test environment setup complete")
    return True


def check_databases():
    """Check if required databases are running."""
    print("🔍 Checking database connections...")
    
    # Check Neo4j
    try:
        import neo4j
        driver = neo4j.GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "test")
        )
        driver.verify_connectivity()
        driver.close()
        print("✅ Neo4j connection: OK")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("💡 Start Neo4j: docker compose up neo4j")
    
    # Check PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="ast_viewer_test",
            user="test_user",
            password="test_pass"
        )
        conn.close()
        print("✅ PostgreSQL connection: OK")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("💡 Start PostgreSQL: docker compose up postgres")
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, db=15)
        r.ping()
        print("✅ Redis connection: OK")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Start Redis: docker compose up redis")


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="AST Viewer TDD Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "command",
        choices=["unit", "integration", "neo4j", "performance", "all", "tdd", "coverage", "setup", "check"],
        help="Test command to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--html",
        action="store_true", 
        help="Generate HTML coverage report (with coverage command)"
    )
    
    parser.add_argument(
        "--watch",
        default="src/",
        help="Directory to watch in TDD mode (default: src/)"
    )
    
    args = parser.parse_args()
    
    print("🚀 AST Viewer TDD Test Runner")
    print("=" * 40)
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    # Route to appropriate test function
    success = True
    
    if args.command == "setup":
        success = setup_test_environment()
        
    elif args.command == "check":
        check_databases()
        
    elif args.command == "unit":
        success = run_unit_tests(args.verbose)
        
    elif args.command == "integration":
        success = run_integration_tests(args.verbose)
        
    elif args.command == "neo4j":
        success = run_neo4j_tests(args.verbose)
        
    elif args.command == "performance":
        success = run_performance_tests(args.verbose)
        
    elif args.command == "all":
        success = run_all_tests(args.verbose)
        
    elif args.command == "coverage":
        success = run_coverage_tests(args.html, args.verbose)
        
    elif args.command == "tdd":
        success = run_tdd_mode(args.watch, args.verbose)
    
    if success:
        print("✅ Tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

