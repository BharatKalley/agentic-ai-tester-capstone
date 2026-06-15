"""Agent C execution helper: run generated Playwright tests via real Playwright CLI."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _npx_command() -> str:
    if os.name == "nt":
        return "npx.cmd" if shutil.which("npx.cmd") else "npx"
    return "npx"


def _parse_json_report(output: str, return_code: int) -> Dict[str, Any]:
    """Parse Playwright JSON reporter output.

    Playwright's JSON reporter uses stats.expected / unexpected / flaky / skipped,
    not total / passed / failed. Older versions of this project misread those keys.
    """
    try:
        report = json.loads(output)
        stats = report.get("stats", {})
        passed = int(stats.get("expected", stats.get("passed", 0)) or 0)
        failed = int(stats.get("unexpected", stats.get("failed", 0)) or 0)
        flaky = int(stats.get("flaky", 0) or 0)
        skipped = int(stats.get("skipped", 0) or 0)
        total = int(stats.get("total", passed + failed + flaky + skipped) or 0)
        return {
            "test_count": total,
            "passed_count": passed,
            "failed_count": failed,
            "flaky_count": flaky,
            "skipped_count": skipped,
            "status": "PASSED" if return_code == 0 and failed == 0 else "FAILED",
        }
    except Exception:
        return {
            "test_count": 0,
            "passed_count": 0,
            "failed_count": 0 if return_code == 0 else 1,
            "flaky_count": 0,
            "skipped_count": 0,
            "status": "PASSED" if return_code == 0 else "FAILED",
        }


def run_single_test(test_file_path: str) -> Dict[str, Any]:
    start_time = time.time()
    root = _project_root()
    abs_path = (root / test_file_path).resolve() if not Path(test_file_path).is_absolute() else Path(test_file_path).resolve()
    if not abs_path.exists():
        return {"status": "FAILED", "error": f"Test file not found: {abs_path}", "test_file": str(test_file_path), "execution_time": 0}

    relative_test_path = os.path.relpath(abs_path, root).replace("\\", "/")
    command = [_npx_command(), "playwright", "test", relative_test_path, "--reporter=json", "--workers=1"]
    try:
        completed = subprocess.run(command, cwd=str(root), capture_output=True, text=True, check=False, timeout=120)
        output = (completed.stdout or "") + (completed.stderr or "")
        parsed = _parse_json_report(completed.stdout or output, completed.returncode)
        return {
            **parsed,
            "test_file": str(test_file_path),
            "return_code": completed.returncode,
            "execution_time": time.time() - start_time,
            "output": output[-6000:],
            "error": None if parsed["status"] == "PASSED" else (output[-6000:] or "Playwright test run failed"),
        }
    except FileNotFoundError:
        return {"status": "ERROR", "error": "npx was not found. Install Node.js LTS, then run npm install and npx playwright install.", "test_file": str(test_file_path), "execution_time": time.time() - start_time}
    except subprocess.TimeoutExpired:
        return {"status": "ERROR", "error": "Playwright test timed out after 120 seconds.", "test_file": str(test_file_path), "execution_time": time.time() - start_time}
    except Exception as exc:
        return {"status": "ERROR", "error": str(exc), "test_file": str(test_file_path), "execution_time": time.time() - start_time}


def run_all_tests(test_dir: str = "generated_tests") -> Dict[str, Any]:
    start_time = time.time()
    root = _project_root()
    path = (root / test_dir).resolve() if not Path(test_dir).is_absolute() else Path(test_dir).resolve()
    if not path.exists():
        return {"status": "FAILED", "error": f"Test directory not found: {path}", "total_tests": 0, "passed": 0, "failed": 0}

    relative_path = os.path.relpath(path, root).replace("\\", "/")
    command = [_npx_command(), "playwright", "test", relative_path, "--reporter=json", "--workers=1"]
    try:
        completed = subprocess.run(command, cwd=str(root), capture_output=True, text=True, check=False, timeout=600)
        output = (completed.stdout or "") + (completed.stderr or "")
        parsed = _parse_json_report(completed.stdout or output, completed.returncode)
        return {
            "status": parsed["status"],
            "total_tests": parsed["test_count"],
            "passed": parsed["passed_count"],
            "failed": parsed["failed_count"],
            "skipped": parsed["skipped_count"],
            "return_code": completed.returncode,
            "execution_time": time.time() - start_time,
            "output": output[-10000:],
            "error": None if parsed["status"] == "PASSED" else (output[-10000:] or "Playwright test run failed"),
        }
    except FileNotFoundError:
        return {"status": "ERROR", "error": "npx was not found. Install Node.js LTS, then run npm install and npx playwright install.", "total_tests": 0, "passed": 0, "failed": 0}
    except subprocess.TimeoutExpired:
        return {"status": "ERROR", "error": "Playwright run timed out after 10 minutes.", "total_tests": 0, "passed": 0, "failed": 0}


def run_test_with_retry(test_file_path: str, max_retries: int = 5) -> Dict[str, Any]:
    last = {}
    for attempt in range(1, max_retries + 1):
        last = run_single_test(test_file_path)
        last["attempts"] = attempt
        if last.get("status") == "PASSED":
            return last
    last["total_attempts"] = max_retries
    return last
