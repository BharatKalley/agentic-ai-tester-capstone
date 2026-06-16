"""Cleanup helpers for generated workflow outputs."""
from __future__ import annotations

import shutil
from pathlib import Path

OUTPUT_DIRS = [
    "generated_tests", "reports", "requirements", "feedback",
    "coverage", "execution", "test-results", "playwright-report",
]

PROJECT_DIRS = [
    "generated_tests", "reports", "requirements", "feedback", "coverage", "execution",
]


def ensure_project_dirs() -> None:
    for folder in PROJECT_DIRS:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        (path / ".gitkeep").touch(exist_ok=True)


def clean_workflow_outputs() -> None:
    for folder in OUTPUT_DIRS:
        path = Path(folder)
        if path.exists():
            shutil.rmtree(path)
    ensure_project_dirs()
