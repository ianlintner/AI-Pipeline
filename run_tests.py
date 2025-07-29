#!/usr/bin/env python3
"""
Test runner script for the Bug Report Triage Service

This script provides a convenient way to run different types of tests
and code quality checks locally before pushing to CI.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print("=" * 60)

    result = subprocess.run(cmd, shell=True, capture_output=False)

    if result.returncode != 0:
        print(f"❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description} passed")
        return True


def install_dependencies():
    """Install test dependencies"""
    print("Installing dependencies...")
    return run_command(
        "pip install -r requirements.txt && pip install -r requirements-test.txt",
        "Installing dependencies",
    )


def run_linting():
    """Run code linting and formatting checks"""
    success = True

    # Black formatting check
    success &= run_command("black --check --diff .", "Black formatting check")

    # isort import sorting check
    success &= run_command("isort --check-only --diff .", "isort import sorting check")

    # Flake8 linting
    success &= run_command("flake8 .", "Flake8 linting")

    # MyPy type checking
    success &= run_command(
        "mypy . --ignore-missing-imports --no-strict-optional", "MyPy type checking"
    )

    return success


def run_unit_tests():
    """Run unit tests with coverage"""
    return run_command(
        "pytest tests/unit/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=html",
        "Unit tests with coverage",
    )


def run_integration_tests():
    """Run integration tests"""
    return run_command(
        'pytest tests/integration/ -v --tb=short -m "integration and not slow"',
        "Integration tests",
    )


def run_all_tests():
    """Run all tests"""
    return run_command(
        "pytest tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=html",
        "All tests with coverage",
    )


def run_security_checks():
    """Run security checks"""
    success = True

    # Safety check for known vulnerabilities
    success &= run_command("safety check", "Safety vulnerability check")

    # Bandit security linting
    success &= run_command("bandit -r . -ll", "Bandit security linting")

    return success


def format_code():
    """Format code with black and isort"""
    success = True

    success &= run_command("black .", "Black code formatting")
    success &= run_command("isort .", "isort import sorting")

    return success


def main():
    parser = argparse.ArgumentParser(description="Run tests and code quality checks")
    parser.add_argument(
        "--install-deps", action="store_true", help="Install dependencies"
    )
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests"
    )
    parser.add_argument("--all-tests", action="store_true", help="Run all tests")
    parser.add_argument("--security", action="store_true", help="Run security checks")
    parser.add_argument("--format", action="store_true", help="Format code")
    parser.add_argument(
        "--full", action="store_true", help="Run full CI pipeline locally"
    )

    args = parser.parse_args()

    # If no specific arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        return

    success = True

    if args.install_deps or args.full:
        success &= install_dependencies()

    if args.format:
        success &= format_code()

    if args.lint or args.full:
        success &= run_linting()

    if args.unit or args.full:
        success &= run_unit_tests()

    if args.integration or args.full:
        success &= run_integration_tests()

    if args.all_tests:
        success &= run_all_tests()

    if args.security or args.full:
        success &= run_security_checks()

    print(f"\n{'='*60}")
    if success:
        print("🎉 All checks passed!")
        sys.exit(0)
    else:
        print("❌ Some checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
