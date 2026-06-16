"""Summary report builder for Agent C final output."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

FAILED = "FAILED_AFTER_MAX_ATTEMPTS"
PASSED = "PASSED"
MANUAL = "MANUAL_REVIEW_REQUIRED"


def _csv(items: List[str]) -> str:
    return ", ".join(f"`{item}`" for item in items) or "_None_"


def _issue_lines(results: List[Dict]) -> str:
    lines = []
    for result in results:
        validation = str(result.get("validation", ""))
        if result.get("final_outcome") != FAILED and not validation.upper().startswith("FAIL"):
            continue

        req = result.get("requirement", {})
        feedback = result.get("agent_c_feedback", {})
        suggestion = feedback.get("instruction_to_agent_b", "Review and regenerate this script.")
        lines.append(
            f"- **[{result.get('final_outcome')}]** `{req.get('id')}`: {validation}\n"
            f"  > Fix: {suggestion}"
        )

    return "\n".join(lines) or "_No issues found._"


def build_markdown_report(coverage: Dict, results: List[Dict]) -> str:
    summary = coverage["summary"]
    matrix = coverage["matrix"]
    approved = "✅ YES" if summary["approved"] else "❌ NO"
    manual = [rid for rid, row in matrix.items() if row.get("manual_review_required")]

    summary_text = (
        f"Agent C reviewed {summary['total_requirements']} requirements. "
        f"{summary['tests_passed']} executable tests passed, "
        f"{len(summary['failed_requirements'])} failed, and "
        f"{summary['manual_review_required']} NFRs require manual review."
    )

    return f"""# Agent C Critic Report

## Summary
{summary_text}

## Coverage Metrics
| Metric | Value |
|--------|-------|
| Total Requirements | {summary['total_requirements']} |
| Tests Generated | {summary['tests_generated']} |
| Tests Executed | {summary['tests_executed']} |
| Tests Passed | {summary['tests_passed']} |
| Manual Review Required | {summary['manual_review_required']} |
| Coverage Percentage | **{summary['coverage_percent']:.1f}%** |
| Pass Percentage | **{summary['pass_percent']:.1f}%** |
| Approved | {approved} |

## Missing Requirements
{_csv(summary['missing_requirements'])}

## Failed Requirements
{_csv(summary['failed_requirements'])}

## NFR Manual Review
{_csv(manual)}

## Hallucinated Scripts
{_csv(summary['hallucinated_scripts'])}

## Detailed Issues
{_issue_lines(results)}
"""


def write_summary_reports(coverage: Dict, results: List[Dict]) -> Dict:
    Path("reports").mkdir(exist_ok=True)
    Path("reports/final_report.md").write_text(
        build_markdown_report(coverage, results),
        encoding="utf-8",
    )
    return {
        "summary": coverage["summary"],
        "markdown_report": "reports/final_report.md",
        "detailed_report": "reports/final_report_detailed.json",
    }
