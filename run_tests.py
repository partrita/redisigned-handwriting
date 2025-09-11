#!/usr/bin/env python3
"""
Test runner script for transcription-game.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", coverage=True, verbose=False):
    """
    Run tests with specified options.

    Args:
        test_type: Type of tests to run ("unit", "integration", "all")
        coverage: Whether to generate coverage report
        verbose: Whether to run in verbose mode
    """

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test selection
    if test_type == "unit":
        cmd.extend(
            [
                "tests/test_text_processor.py",
                "tests/test_pdf_generator.py",
                "tests/test_font_manager.py",
                "tests/test_rate_limiter.py",
            ]
        )
    elif test_type == "integration":
        cmd.append("tests/test_integration.py")
    else:  # all
        cmd.append("tests/")

    # Add coverage options
    if coverage:
        cmd.extend(
            [
                "--cov=src/handwriting_transcription",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-fail-under=80",
            ]
        )

    # Add verbose option
    if verbose:
        cmd.append("-v")

    # Add other useful options
    cmd.extend(
        [
            "--strict-markers",
            "--strict-config",
            "-x",  # Stop on first failure
            "--tb=short",  # Shorter traceback format
        ]
    )

    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run transcription-game tests")

    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run (default: all)",
    )

    parser.add_argument(
        "--no-coverage", action="store_true", help="Skip coverage reporting"
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running",
    )

    args = parser.parse_args()

    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
            )
            print("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install dependencies: {e}")
            return 1

    # Run tests
    return run_tests(
        test_type=args.type, coverage=not args.no_coverage, verbose=args.verbose
    )


if __name__ == "__main__":
    sys.exit(main())
