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
from utils.summary_report_utils import write_summary_reports

MAX_RETRIES = 5
ROOT_DIRS = ["generated_tests", "reports", "requirements", "feedback", "coverage", "execution"]
PASSED, FAILED, MANUAL, PASS_NFR = "PASSED", "FAILED_AFTER_MAX_ATTEMPTS", "MANUAL_REVIEW_REQUIRED", "PASS_NFR_REVIEW"
EDGE_KEYS = ["invalid", "error", "empty", "denies", "random", "edge", "negative"]

def ensure_project_dirs() -> None:
    for folder in ROOT_DIRS:
        path = Path(folder)
        path.mkdir(exist_ok=True)
        (path / ".gitkeep").touch(exist_ok=True)
        
def _write_json(path: str | Path, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    
def _same_requirement(a: Dict, b: Dict) -> bool:
    return a.get("id") == b.get("id") or (a.get("feature"), a.get("endpoint")) == (b.get("feature"), b.get("endpoint"))

def _is_nfr(req: Dict) -> bool:
    return str(req.get("id", "")).upper().startswith("NFR") or str(req.get("type", "")).lower().startswith("non")

def _is_pass(validation: str) -> bool:
    return validation.upper().startswith("PASS")

def _accepted(req: Dict, validation: str, execution: Optional[Dict], execute_tests: bool) -> bool:
    if _is_nfr(req):
        return validation.upper().startswith(PASS_NFR)
    return _is_pass(validation) and (not execute_tests or bool(execution and execution.get("status") == PASSED))

def _final_outcome(req: Dict, validation: str, execution: Optional[Dict], execute_tests: bool) -> str:
    if _is_nfr(req) and validation.upper().startswith(PASS_NFR):
        return MANUAL
    return PASSED if _accepted(req, validation, execution, execute_tests) else FAILED

def _failure_feedback(validation: str, execution: Optional[Dict]) -> Dict:
    issues = []
    if validation and not _is_pass(validation):
        issues.append("Static validation failed: " + validation)
    if execution and execution.get("status") != PASSED:
        err = execution.get("error") or execution.get("output") or "Playwright execution failed"
        issues.append("Playwright execution failed. Fix only this requirement. Error/output: " + str(err)[-2500:])
    return {"issues": issues, "instruction_to_agent_b": "Regenerate only this failed requirement. Do not regenerate already passed scripts. Use actual visible UI text and stable Playwright locators. Never assert SRS prose. Avoid fixed sleeps; use role, text, id, and CSS locators that exist on the page."}

def _run_if_needed(req: Dict, file_path: str, validation: str, execute_tests: bool, attempt: int) -> Optional[Dict]:
    if not (execute_tests and _is_pass(validation) and not _is_nfr(req)):
        return None
    execution = run_single_test(file_path)
    _write_json(Path("execution") / f"{Path(file_path).stem}_attempt_{attempt}.json", execution)
    return execution

def _run_attempt(req: Dict, feedback: str, attempt: int, execute_tests: bool) -> Dict:
    script = generate_playwright_script(req, feedback=feedback)
    validation = validate_script(req, script)
    file_path = save_script(req, script)
    execution = _run_if_needed(req, file_path, validation, execute_tests, attempt)
    accepted = _accepted(req, validation, execution, execute_tests)
    record = {"attempt": attempt, "requirement_id": req.get("id"), "script_file": file_path, "static_validation": validation, "execution_status": None if execution is None else execution.get("status"), "agent_c_decision": "ACCEPT" if accepted else "REJECT_AND_FEEDBACK_TO_AGENT_B"}
    return {"file_path": file_path, "validation": validation, "execution": execution, "accepted": accepted, "record": record}

def run_workflow_for_requirement(req: Dict, execute_tests: bool = True) -> Dict:
    ensure_project_dirs()
    feedback_text, feedback, attempts = "", {}, []
    result = {"file_path": "", "validation": "FAIL: Not generated yet.", "execution": None}
    for attempt in range(1, MAX_RETRIES + 1):
        result = _run_attempt(req, feedback_text, attempt, execute_tests)
        attempts.append(result["record"])
        _write_json(Path("reports") / f"iteration_{req.get('id', 'REQ')}_{attempt}.json", result["record"])
        if result["accepted"]:
            feedback = {"issues": [], "instruction_to_agent_b": "No regeneration needed. Script accepted by Agent C."}
            break
        feedback = _failure_feedback(result["validation"], result["execution"])
        feedback_text = json.dumps(feedback)
        _write_json(Path("feedback") / f"{req.get('id', 'REQ')}_attempt_{attempt}.json", feedback)
    return {"requirement": req, "script_file": result["file_path"], "validation": result["validation"], "execution": result["execution"], "attempts": len(attempts), "retries": max(0, len(attempts) - 1), "attempt_history": attempts, "agent_c_feedback": feedback, "final_outcome": _final_outcome(req, result["validation"], result["execution"], execute_tests)}

def _matrix_row(req: Dict, latest: Dict) -> Dict:
    validation = str(latest.get("validation", ""))
    text = (req.get("expected", "") + req.get("scenario", "")).lower()
    return {"endpoint": req.get("endpoint"), "feature": req.get("feature"), "test_exists": bool(latest.get("script_file")), "script_file": latest.get("script_file"), "executed": latest.get("execution") is not None, "passed": latest.get("final_outcome") == PASSED, "manual_review_required": latest.get("final_outcome") == MANUAL, "attempts": latest.get("attempts", 0), "hallucination_detected": validation.upper().startswith("FAIL") and "hallucinat" in validation.lower(), "edge_case_candidate": any(k in text for k in EDGE_KEYS)}

def _summary(matrix: Dict) -> Dict:
    total = len(matrix)
    summary = {"total_requirements": total, "tests_generated": sum(v["test_exists"] for v in matrix.values()), "tests_executed": sum(v["executed"] for v in matrix.values()), "tests_passed": sum(v["passed"] for v in matrix.values()), "manual_review_required": sum(v["manual_review_required"] for v in matrix.values()), "missing_requirements": [rid for rid, v in matrix.items() if not v["test_exists"]], "failed_requirements": [rid for rid, v in matrix.items() if v["test_exists"] and not v["passed"] and not v["manual_review_required"]], "hallucinated_scripts": [rid for rid, v in matrix.items() if v["hallucination_detected"]]}
    summary["coverage_percent"] = round(summary["tests_generated"] / total * 100, 2) if total else 0
    summary["pass_percent"] = round(summary["tests_passed"] / total * 100, 2) if total else 0
    summary["approved"] = not summary["missing_requirements"] and not summary["failed_requirements"] and not summary["hallucinated_scripts"]
    return summary

def build_coverage_matrix(requirements: List[Dict], results: List[Dict]) -> Dict:
    matrix = {}
    for req in requirements:
        rid = req.get("id", "UNKNOWN")
        latest = next((r for r in reversed(results) if r.get("requirement", {}).get("id") == rid), {})
        matrix[rid] = _matrix_row(req, latest)
    return {"summary": _summary(matrix), "matrix": matrix}

def _finalize(requirements: List[Dict], results: List[Dict], report_name: str) -> List[Dict]:
    coverage = build_coverage_matrix(requirements, results)
    summary_report = write_summary_reports(coverage, results)
    _write_json("coverage/coverage_matrix.json", coverage)
    _write_json("reports/final_report.json", summary_report)
    _write_json("reports/final_report_detailed.json", {"coverage": coverage, "results": results})
    ReportManager().save_report(summary_report, report_name)
    return results

def run_workflow(pdf_path: str, execute_tests: bool = True, max_requirements: Optional[int] = None, clean: bool = True) -> List[Dict]:
    ensure_project_dirs()
    if clean:
        clean_generated_outputs(); ensure_project_dirs()
    requirements = extract_requirements(pdf_path)
    requirements = requirements[:max_requirements] if max_requirements else requirements
    _write_json("requirements/extracted_requirements.json", requirements)
    return _finalize(requirements, [run_workflow_for_requirement(req, execute_tests) for req in requirements], "latest_validation_report")

def run_execution_only(test_dir: str = "generated_tests"):
    ensure_project_dirs()
    result = run_all_tests(test_dir)
    _write_json("execution/playwright_results.json", result)
    return result

def run_workflow_with_selective_regeneration(pdf_path: str, previous_results: Optional[list] = None, execute_tests: bool = True):
    ensure_project_dirs()
    requirements, old, results = extract_requirements(pdf_path), previous_results or [], []
    for req in requirements:
        previous = next((r for r in old if _same_requirement(r.get("requirement", {}), req)), None)
        results.append(previous if previous and previous.get("final_outcome") == PASSED else run_workflow_for_requirement(req, execute_tests))
    return _finalize(requirements, results, "latest_selective_regeneration_report")
