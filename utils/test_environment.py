"""
Test environment management utilities.
Handles setup, verification, and cleanup for test execution.
"""

import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any


class TestEnvironment:
    """Manage test execution environment."""
    
    @staticmethod
    def check_playwright_python_installed() -> bool:
        """Check if Playwright Python package is installed."""
        try:
            import playwright
            return True
        except ImportError:
            return False
    
    @staticmethod
    def check_pytest_installed() -> bool:
        """Check if pytest is installed."""
        try:
            import pytest
            return True
        except ImportError:
            return False
    
    @staticmethod
    def check_python_version() -> Tuple[bool, str]:
        """Check if Python version is compatible."""
        major, minor = sys.version_info.major, sys.version_info.minor
        
        if major < 3 or (major == 3 and minor < 8):
            return False, f"Python 3.8+ required, found {major}.{minor}"
        
        return True, f"Python {major}.{minor} OK"
    
    @staticmethod
    def verify_test_directory(test_dir: str = "generated_tests") -> Tuple[bool, str]:
        """
        Verify test directory exists and contains test files.
        
        Returns:
            Tuple of (valid: bool, message: str)
        """
        path = Path(test_dir)
        
        if not path.exists():
            return False, f"Test directory does not exist: {test_dir}"
        
        if not path.is_dir():
            return False, f"Path is not a directory: {test_dir}"
        
        test_files = list(path.glob("*.spec.ts"))
        
        if not test_files:
            return False, f"No test files found in {test_dir}"
        
        return True, f"Found {len(test_files)} test files"
    
    @staticmethod
    def full_environment_check() -> Dict[str, Any]:
        """
        Perform comprehensive environment check.
        
        Returns:
            Dictionary with check results
        """
        python_ok, python_msg = TestEnvironment.check_python_version()
        playwright_ok = TestEnvironment.check_playwright_python_installed()
        pytest_ok = TestEnvironment.check_pytest_installed()
        test_dir_ok, _ = TestEnvironment.verify_test_directory()
        
        checks = {
            "python_version": python_ok,
            "playwright_installed": playwright_ok,
            "pytest_installed": pytest_ok,
            "test_directory_valid": test_dir_ok
        }
        
        all_checks_passed = all([python_ok, playwright_ok])
        
        missing = []
        if not python_ok:
            missing.append("Python 3.8+")
        if not playwright_ok:
            missing.append("playwright Python package")
        
        return {
            "all_checks_passed": all_checks_passed,
            "checks": checks,
            "missing_dependencies": missing,
            "python_version_message": python_msg
        }
    
    @staticmethod
    def setup_environment() -> Tuple[bool, str]:
        """
        Verify test environment is ready.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        status_messages = []
        
        # Check Python version
        python_ok, python_msg = TestEnvironment.check_python_version()
        if not python_ok:
            return False, python_msg
        status_messages.append(f"✓ {python_msg}")
        
        # Check Playwright Python package
        if not TestEnvironment.check_playwright_python_installed():
            return False, (
                "Playwright Python package not installed. "
                "Run: pip install playwright"
            )
        status_messages.append("✓ Playwright Python package installed")
        
        # Check test directory
        test_dir = Path("generated_tests")
        if not test_dir.exists():
            test_dir.mkdir(parents=True, exist_ok=True)
            status_messages.append("✓ Created test directory")
        else:
            status_messages.append("✓ Test directory exists")
        
        return True, "\n".join(status_messages)


class TestRunner:
    """Utility class for running tests with various options."""
    
    @staticmethod
    def get_test_files(test_dir: str = "generated_tests") -> List[str]:
        """Get list of all test files in a directory."""
        path = Path(test_dir)
        return sorted([str(f) for f in path.glob("*.spec.ts")])
    
    @staticmethod
    def count_tests(test_dir: str = "generated_tests") -> int:
        """Count number of test files."""
        return len(TestRunner.get_test_files(test_dir))
    
    @staticmethod
    def validate_test_file(filepath: str) -> Tuple[bool, str]:
        """
        Validate that a test file exists and is readable.
        
        Returns:
            Tuple of (valid: bool, message: str)
        """
        path = Path(filepath)
        
        if not path.exists():
            return False, f"File does not exist: {filepath}"
        
        if not path.is_file():
            return False, f"Path is not a file: {filepath}"
        
        if not filepath.endswith(".spec.ts"):
            return False, f"File is not a test file (*.spec.ts): {filepath}"
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if len(content) == 0:
                    return False, f"Test file is empty: {filepath}"
                if "test" not in content.lower():
                    return False, f"No test definitions found in: {filepath}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
        
        return True, f"Valid test file: {filepath}"
    
    @staticmethod
    def estimate_execution_time(num_tests: int, avg_time_per_test: float = 5.0) -> float:
        """Estimate total execution time in seconds."""
        return num_tests * avg_time_per_test


def print_environment_report(check_result: Dict[str, Any]) -> None:
    """Print a formatted environment check report."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT CHECK REPORT")
    print("=" * 60)
    
    print(f"\nOverall Status: {'✅ PASS' if check_result['all_checks_passed'] else '❌ FAIL'}")
    
    print("\nIndividual Checks:")
    for check_name, passed in check_result["checks"].items():
        status = "✅ PASS" if passed else "❌ FAIL"
        formatted_name = check_name.replace("_", " ").title()
        print(f"  {status} - {formatted_name}")
    
    if check_result["missing_dependencies"]:
        print(f"\nMissing Dependencies:")
        for dep in check_result["missing_dependencies"]:
            print(f"  - {dep}")
        print("\nTo fix, run:")
        print(f"  pip install {' '.join(dep.lower() for dep in check_result['missing_dependencies'])}")
    
    if "python_version_message" in check_result:
        print(f"\nPython Version: {check_result['python_version_message']}")
    
    print("\n" + "=" * 60)
