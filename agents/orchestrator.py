"""Capstone orchestrator for Agent A, Agent B and Agent C.

Agent A extracts atomic requirements from an SRS PDF.
Agent B generates Playwright TypeScript tests.
Agent C validates, executes, analyzes coverage, writes feedback, and asks Agent B
for selective regeneration up to five attempts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from agents.extractor_agent import extract_requirements
from agents.playwright_agent import generate_playwright_script
from agents.validator_agent import validate_script
from agents.executor_agent import run_single_test, run_all_tests
from utils.file_utils import save_script, clean_generated_outputs
from utils.test_report_utils import ReportManager

MAX_RETRIES = 5
ROOT_DIRS = ["generated_tests", "reports", "requirements", "feedback", "coverage", "execution"]


def ensure_project_dirs() -> None:
    for folder in ROOT_DIRS:
        Path(folder).mkdir(exist_ok=True)
        keep = Path(folder) / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")


def _write_json(path: str | Path, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _same_requirement(a: Dict, b: Dict) -> bool:
    return a.get("id") == b.get("id") or (a.get("feature") == b.get("feature") and a.get("endpoint") == b.get("endpoint"))


def _failure_feedback(validation: str, execution: Optional[Dict]) -> Dict:
    issues: List[str] = []
    if validation and not validation.upper().startswith("PASS"):
        issues.append("Static validation failed: " + validation)
    if execution and execution.get("status") != "PASSED":
        err = execution.get("error") or execution.get("output") or "Playwright execution failed"
        issues.append("Playwright execution failed. Fix only this requirement. Error/output: " + str(err)[-2500:])
    return {
        "issues": issues,
        "instruction_to_agent_b": (
            "Regenerate only this failed requirement. Do not regenerate already passed scripts. "
            "Use actual visible UI text and stable Playwright locators. Never assert SRS prose. "
            "Avoid fixed sleeps; use role, text, id, and CSS locators that exist on the page."
        ),
    }


def run_workflow_for_requirement(req: Dict, execute_tests: bool = True) -> Dict:
    ensure_project_dirs()
    feedback_text = ""
    attempts: List[Dict] = []
    last_file_path = ""
    last_validation = "FAIL: Not generated yet."
    last_execution: Optional[Dict] = None
    final_feedback: Dict = {}

    for attempt_no in range(1, MAX_RETRIES + 1):
        script = generate_playwright_script(req, feedback=feedback_text)
        validation = validate_script(req, script)
        file_path = save_script(req, script)
        execution = None

        if validation.upper().startswith("PASS") and execute_tests:
            execution = run_single_test(file_path)
            _write_json(Path("execution") / (Path(file_path).stem + f"_attempt_{attempt_no}.json"), execution)

        passed_static = validation.upper().startswith("PASS")
        passed_execution = (not execute_tests) or (execution and execution.get("status") == "PASSED")
        attempt_record = {
            "attempt": attempt_no,
            "requirement_id": req.get("id"),
            "script_file": file_path,
            "static_validation": validation,
            "execution_status": None if execution is None else execution.get("status"),
            "agent_c_decision": "ACCEPT" if passed_static and passed_execution else "REJECT_AND_FEEDBACK_TO_AGENT_B",
        }
        attempts.append(attempt_record)
        _write_json(Path("reports") / f"iteration_{req.get('id','REQ')}_{attempt_no}.json", attempt_record)

        last_file_path, last_validation, last_execution = file_path, validation, execution
        if passed_static and passed_execution:
            final_feedback = {"issues": [], "instruction_to_agent_b": "No regeneration needed. Script accepted by Agent C."}
            break

        final_feedback = _failure_feedback(validation, execution)
        feedback_text = json.dumps(final_feedback)
        _write_json(Path("feedback") / f"{req.get('id','REQ')}_attempt_{attempt_no}.json", final_feedback)

    final_outcome = "PASSED" if last_validation.upper().startswith("PASS") and ((not execute_tests) or (last_execution and last_execution.get("status") == "PASSED")) else "FAILED_AFTER_MAX_ATTEMPTS"
    return {
        "requirement": req,
        "script_file": last_file_path,
        "validation": last_validation,
        "execution": last_execution,
        "attempts": len(attempts),
        "retries": max(0, len(attempts) - 1),
        "attempt_history": attempts,
        "agent_c_feedback": final_feedback,
        "final_outcome": final_outcome,
    }


def build_coverage_matrix(requirements: List[Dict], results: List[Dict]) -> Dict:
    matrix: Dict[str, Dict] = {}
    for req in requirements:
        rid = req.get("id", "UNKNOWN")
        matches = [r for r in results if r.get("requirement", {}).get("id") == rid]
        latest = matches[-1] if matches else {}
        matrix[rid] = {
            "endpoint": req.get("endpoint"),
            "feature": req.get("feature"),
            "test_exists": bool(latest.get("script_file")),
            "script_file": latest.get("script_file"),
            "executed": latest.get("execution") is not None,
            "passed": latest.get("final_outcome") == "PASSED",
            "attempts": latest.get("attempts", 0),
            "hallucination_detected": "hallucinat" in str(latest.get("validation", "")).lower(),
            "edge_case_candidate": any(k in (req.get("expected", "") + req.get("scenario", "")).lower() for k in ["invalid", "error", "empty", "denies", "random", "edge", "negative"]),
        }
    total = len(matrix)
    covered = sum(1 for v in matrix.values() if v["test_exists"])
    executed = sum(1 for v in matrix.values() if v["executed"])
    passed = sum(1 for v in matrix.values() if v["passed"])
    missing = [rid for rid, v in matrix.items() if not v["test_exists"]]
    failed = [rid for rid, v in matrix.items() if v["test_exists"] and not v["passed"]]
    return {
        "summary": {
            "total_requirements": total,
            "tests_generated": covered,
            "tests_executed": executed,
            "tests_passed": passed,
            "coverage_percent": round((covered / total * 100), 2) if total else 0,
            "pass_percent": round((passed / total * 100), 2) if total else 0,
            "missing_requirements": missing,
            "failed_requirements": failed,
        },
        "matrix": matrix,
    }


def run_workflow(pdf_path: str, execute_tests: bool = True, max_requirements: Optional[int] = None, clean: bool = True) -> List[Dict]:
    ensure_project_dirs()
    if clean:
        clean_generated_outputs()
        ensure_project_dirs()

    requirements = extract_requirements(pdf_path)
    if max_requirements:
        requirements = requirements[:max_requirements]
    _write_json("requirements/extracted_requirements.json", requirements)

    final_results = [run_workflow_for_requirement(req, execute_tests=execute_tests) for req in requirements]
    coverage = build_coverage_matrix(requirements, final_results)
    _write_json("coverage/coverage_matrix.json", coverage)
    _write_json("reports/final_report.json", {"coverage": coverage, "results": final_results})
    ReportManager().save_report({"coverage": coverage, "results": final_results}, "latest_validation_report")
    return final_results


def run_execution_only(test_dir: str = "generated_tests"):
    ensure_project_dirs()
    result = run_all_tests(test_dir)
    _write_json("execution/playwright_results.json", result)
    return result


def run_workflow_with_selective_regeneration(pdf_path: str, previous_results: Optional[list] = None, execute_tests: bool = True):
    ensure_project_dirs()
    requirements = extract_requirements(pdf_path)
    final_results: List[Dict] = []
    previous_results = previous_results or []
    for req in requirements:
        previous = next((r for r in previous_results if _same_requirement(r.get("requirement", {}), req)), None)
        if previous and previous.get("final_outcome") == "PASSED":
            final_results.append(previous)
            continue
        final_results.append(run_workflow_for_requirement(req, execute_tests=execute_tests))
    coverage = build_coverage_matrix(requirements, final_results)
    _write_json("coverage/coverage_matrix.json", coverage)
    _write_json("reports/final_report.json", {"coverage": coverage, "results": final_results})
    ReportManager().save_report({"coverage": coverage, "results": final_results}, "latest_selective_regeneration_report")
    return final_results
