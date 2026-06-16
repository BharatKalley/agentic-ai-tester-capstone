"""Agent C execution helper: run generated Playwright tests via real Playwright CLI."""
from __future__ import annotations

import json, os, shutil, subprocess, time
from pathlib import Path
from typing import Any, Dict


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _npx_command() -> str:
    return "npx.cmd" if os.name == "nt" and shutil.which("npx.cmd") else "npx"


def _parse_json_report(output: str, return_code: int) -> Dict[str, Any]:
    try:
        stats = json.loads(output).get("stats", {})
        passed = int(stats.get("expected", stats.get("passed", 0)) or 0)
        failed = int(stats.get("unexpected", stats.get("failed", 0)) or 0)
        flaky = int(stats.get("flaky", 0) or 0)
        skipped = int(stats.get("skipped", 0) or 0)
        total = int(stats.get("total", passed + failed + flaky + skipped) or 0)
    except Exception:
        passed, failed, flaky, skipped, total = (0, 0 if return_code == 0 else 1, 0, 0, 0)
    return {
        "test_count": total,
        "passed_count": passed,
        "failed_count": failed,
        "flaky_count": flaky,
        "skipped_count": skipped,
        "status": "PASSED" if return_code == 0 and failed == 0 else "FAILED",
    }


def _run_playwright(target: str, timeout: int) -> Dict[str, Any]:
    start, root = time.time(), _project_root()
    path = (root / target).resolve() if not Path(target).is_absolute() else Path(target).resolve()
    if not path.exists():
        return {"status": "FAILED", "error": f"Path not found: {path}", "execution_time": 0}

    rel = os.path.relpath(path, root).replace("\\", "/")
    command = [_npx_command(), "playwright", "test", rel, "--reporter=json", "--workers=1"]
    try:
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False, timeout=timeout)
        output = (completed.stdout or "") + (completed.stderr or "")
        parsed = _parse_json_report(completed.stdout or output, completed.returncode)
        return {
            **parsed,
            "return_code": completed.returncode,
            "execution_time": time.time() - start,
            "output": output[-10000:],
            "error": None if parsed["status"] == "PASSED" else (output[-10000:] or "Playwright test run failed"),
        }
    except FileNotFoundError:
        return {"status": "ERROR", "error": "npx was not found. Install Node.js LTS, run npm install, then npx playwright install.", "execution_time": time.time() - start}
    except subprocess.TimeoutExpired:
        return {"status": "ERROR", "error": f"Playwright run timed out after {timeout} seconds.", "execution_time": time.time() - start}


def run_single_test(test_file_path: str) -> Dict[str, Any]:
    result = _run_playwright(test_file_path, timeout=120)
    return {**result, "test_file": str(test_file_path)}


def run_all_tests(test_dir: str = "generated_tests") -> Dict[str, Any]:
    result = _run_playwright(test_dir, timeout=600)
    return {
        "status": result.get("status"),
        "total_tests": result.get("test_count", 0),
        "passed": result.get("passed_count", 0),
        "failed": result.get("failed_count", 0),
        "skipped": result.get("skipped_count", 0),
        **{k: v for k, v in result.items() if k not in {"test_count", "passed_count", "failed_count", "skipped_count"}},
    }


def run_test_with_retry(test_file_path: str, max_retries: int = 5) -> Dict[str, Any]:
    last: Dict[str, Any] = {}
    for attempt in range(1, max_retries + 1):
        last = {**run_single_test(test_file_path), "attempts": attempt}
        if last.get("status") == "PASSED":
            return last
    return {**last, "total_attempts": max_retries}
