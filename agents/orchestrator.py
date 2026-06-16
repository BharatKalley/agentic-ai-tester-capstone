"""Capstone orchestrator for Agent A, Agent B and Agent C."""
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
        path = Path(folder); path.mkdir(exist_ok=True)
        (path / ".gitkeep").touch(exist_ok=True)


def _write_json(path: str | Path, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _same_requirement(a: Dict, b: Dict) -> bool:
    return a.get("id") == b.get("id") or (a.get("feature"), a.get("endpoint")) == (b.get("feature"), b.get("endpoint"))


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


def _accepted(validation: str, execution: Optional[Dict], execute_tests: bool) -> bool:
    return validation.upper().startswith("PASS") and (not execute_tests or bool(execution and execution.get("status") == "PASSED"))


def _is_nfr(req: Dict) -> bool:
    return str(req.get("id", "")).upper().startswith("NFR") or str(req.get("type", "")).lower().startswith("non")


def run_workflow_for_requirement(req: Dict, execute_tests: bool = True) -> Dict:
    ensure_project_dirs()
    feedback_text, attempts, file_path, validation, execution, final_feedback = "", [], "", "FAIL: Not generated yet.", None, {}
    for attempt_no in range(1, MAX_RETRIES + 1):
        script = generate_playwright_script(req, feedback=feedback_text)
        validation = validate_script(req, script)
        file_path = save_script(req, script)
        execution = None if _is_nfr(req) else (run_single_test(file_path) if validation.upper().startswith("PASS") and execute_tests else None)
        if execution:
            _write_json(Path("execution") / f"{Path(file_path).stem}_attempt_{attempt_no}.json", execution)

        accepted = validation.upper().startswith("PASS_NFR_REVIEW") if _is_nfr(req) else _accepted(validation, execution, execute_tests)
        record = {
            "attempt": attempt_no, "requirement_id": req.get("id"), "script_file": file_path,
            "static_validation": validation, "execution_status": None if execution is None else execution.get("status"),
            "agent_c_decision": "ACCEPT" if accepted else "REJECT_AND_FEEDBACK_TO_AGENT_B",
        }
        attempts.append(record)
        _write_json(Path("reports") / f"iteration_{req.get('id','REQ')}_{attempt_no}.json", record)

        if accepted:
            final_feedback = {"issues": [], "instruction_to_agent_b": "No regeneration needed. Script accepted by Agent C."}
            break
        final_feedback = _failure_feedback(validation, execution)
        feedback_text = json.dumps(final_feedback)
        _write_json(Path("feedback") / f"{req.get('id','REQ')}_attempt_{attempt_no}.json", final_feedback)

    if _is_nfr(req) and validation.upper().startswith("PASS_NFR_REVIEW"):
        final_outcome = "MANUAL_REVIEW_REQUIRED"
    else:
        final_outcome = "PASSED" if _accepted(validation, execution, execute_tests) else "FAILED_AFTER_MAX_ATTEMPTS"
    return {
        "requirement": req, "script_file": file_path, "validation": validation, "execution": execution,
        "attempts": len(attempts), "retries": max(0, len(attempts) - 1), "attempt_history": attempts,
        "agent_c_feedback": final_feedback, "final_outcome": final_outcome,
    }


def build_coverage_matrix(requirements: List[Dict], results: List[Dict]) -> Dict:
    matrix: Dict[str, Dict] = {}
    for req in requirements:
        rid = req.get("id", "UNKNOWN")
        latest = next((r for r in reversed(results) if r.get("requirement", {}).get("id") == rid), {})
        text = (req.get("expected", "") + req.get("scenario", "")).lower()
        matrix[rid] = {
            "endpoint": req.get("endpoint"), "feature": req.get("feature"),
            "test_exists": bool(latest.get("script_file")), "script_file": latest.get("script_file"),
            "executed": latest.get("execution") is not None,
            "passed": latest.get("final_outcome") == "PASSED",
            "manual_review_required": latest.get("final_outcome") == "MANUAL_REVIEW_REQUIRED",
            "attempts": latest.get("attempts", 0),
            "hallucination_detected": str(latest.get("validation", "")).upper().startswith("FAIL") and "hallucinat" in str(latest.get("validation", "")).lower(),
            "edge_case_candidate": any(k in text for k in ["invalid", "error", "empty", "denies", "random", "edge", "negative"]),
        }
    total = len(matrix)
    summary = {
        "total_requirements": total,
        "tests_generated": sum(v["test_exists"] for v in matrix.values()),
        "tests_executed": sum(v["executed"] for v in matrix.values()),
        "tests_passed": sum(v["passed"] for v in matrix.values()),
        "manual_review_required": sum(v.get("manual_review_required", False) for v in matrix.values()),
        "missing_requirements": [rid for rid, v in matrix.items() if not v["test_exists"]],
        "failed_requirements": [rid for rid, v in matrix.items() if v["test_exists"] and not v["passed"] and not v.get("manual_review_required")],
    }
    summary["coverage_percent"] = round(summary["tests_generated"] / total * 100, 2) if total else 0
    summary["pass_percent"] = round(summary["tests_passed"] / total * 100, 2) if total else 0
    return {"summary": summary, "matrix": matrix}


def _finalize(requirements: List[Dict], results: List[Dict], report_name: str) -> List[Dict]:
    coverage = build_coverage_matrix(requirements, results)
    _write_json("coverage/coverage_matrix.json", coverage)
    _write_json("reports/final_report.json", {"coverage": coverage, "results": results})
    ReportManager().save_report({"coverage": coverage, "results": results}, report_name)
    return results


def run_workflow(pdf_path: str, execute_tests: bool = True, max_requirements: Optional[int] = None, clean: bool = True) -> List[Dict]:
    ensure_project_dirs()
    if clean:
        clean_generated_outputs(); ensure_project_dirs()
    requirements = extract_requirements(pdf_path)[:max_requirements] if max_requirements else extract_requirements(pdf_path)
    _write_json("requirements/extracted_requirements.json", requirements)
    return _finalize(requirements, [run_workflow_for_requirement(req, execute_tests) for req in requirements], "latest_validation_report")


def run_execution_only(test_dir: str = "generated_tests"):
    ensure_project_dirs()
    result = run_all_tests(test_dir)
    _write_json("execution/playwright_results.json", result)
    return result


def run_workflow_with_selective_regeneration(pdf_path: str, previous_results: Optional[list] = None, execute_tests: bool = True):
    ensure_project_dirs()
    requirements, previous_results = extract_requirements(pdf_path), previous_results or []
    results = []
    for req in requirements:
        previous = next((r for r in previous_results if _same_requirement(r.get("requirement", {}), req)), None)
        results.append(previous if previous and previous.get("final_outcome") == "PASSED" else run_workflow_for_requirement(req, execute_tests))
    return _finalize(requirements, results, "latest_selective_regeneration_report")
