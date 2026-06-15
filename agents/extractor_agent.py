"""Agent A: extract atomic, testable requirements from an SRS PDF.

This extractor is deterministic so the capstone can run without paid LLM keys.
It recognizes formal FR-* requirement blocks and concise bullet requirements,
normalizes them, infers the target route, and removes duplicates.
"""
from __future__ import annotations

import os
import re
from typing import Dict, List

from parser.pdf_parser import extract_text_from_pdf

BASE_URL = os.getenv("BASE_URL", "https://the-internet.herokuapp.com")

# Longest/specific keywords must come before broad ones like "upload" or "alert".
PATH_BY_KEYWORD = [
    ("add/remove", "/add_remove_elements/"),
    ("add remove", "/add_remove_elements/"),
    ("form authentication", "/login"),
    ("valid credentials", "/login"),
    ("invalid credentials", "/login"),
    ("dynamic controls", "/dynamic_controls"),
    ("dynamic loading", "/dynamic_loading"),
    ("dynamic content", "/dynamic_content"),
    ("file uploader", "/upload"),
    ("file upload", "/upload"),
    ("file download", "/download"),
    ("file downloader", "/download"),
    ("javascript alerts", "/javascript_alerts"),
    ("js alert", "/javascript_alerts"),
    ("js confirm", "/javascript_alerts"),
    ("js prompt", "/javascript_alerts"),
    ("javascript error", "/javascript_error"),
    ("drag and drop", "/drag_and_drop"),
    ("data tables", "/tables"),
    ("sortable data tables", "/tables"),
    ("notification message", "/notification_message_rendered"),
    ("entry ad", "/entry_ad"),
    ("disappearing elements", "/disappearing_elements"),
    ("horizontal slider", "/horizontal_slider"),
    ("context menu", "/context_menu"),
    ("challenging dom", "/challenging_dom"),
    ("exit intent", "/exit_intent"),
    ("jquery ui", "/jqueryui/menu"),
    ("jquery", "/jqueryui/menu"),
    ("infinite scroll", "/infinite_scroll"),
    ("forgot password", "/forgot_password"),
    ("floating menu", "/floating_menu"),
    ("shadow dom", "/shadowdom"),
    ("shifting content", "/shifting_content"),
    ("status codes", "/status_codes"),
    ("checkbox", "/checkboxes"),
    ("dropdown", "/dropdown"),
    ("upload", "/upload"),
    ("alert", "/javascript_alerts"),
    ("tables", "/tables"),
    ("typos", "/typos"),
    ("hovers", "/hovers"),
    ("a/b", "/abtest"),
    ("inputs", "/inputs"),
    ("large", "/large"),
    ("geolocation", "/geolocation"),
    ("frames", "/frames"),
    ("windows", "/windows"),
    ("home page", "/"),
    ("root url", "/"),
    ("footer", "/checkboxes"),
]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip(" •o:-\t")


def _infer_endpoint(text: str) -> str:
    lower = text.lower()
    explicit_paths = re.findall(r"(?<!\w)(/[a-zA-Z0-9_/-]+)(?!\w)", text)
    for path in explicit_paths:
        if path not in {"/", "//"}:
            return path
    if "welcome to the-internet" in lower or "root url" in lower:
        return "/"
    for key, path in PATH_BY_KEYWORD:
        if key in lower:
            return path
    return "/"


def _block_until_next(lines: List[str], start: int) -> str:
    block = [lines[start]]
    for line in lines[start + 1 :]:
        if re.match(r"^FR-[A-Z0-9-]+\s*[–-]", line):
            break
        if re.match(r"^\d+\.\d+(\.\d+)?\s+", line):
            break
        block.append(line)
    return "\n".join(block)


def _extract_field(block: str, label: str) -> str:
    pattern = rf"{label}\s*:?[\s\n]*(.*?)(?=\n\s*(?:Feature Name|Description|Preconditions|User Actions|Expected (?:System )?Behavior|Expected Behavior|Validation|Source text|FR-|\d+\.\d+)|\Z)"
    match = re.search(pattern, block, flags=re.I | re.S)
    return _clean(match.group(1)) if match else ""


def _normalize_requirement(req: Dict[str, str]) -> Dict[str, str]:
    req["feature"] = _clean(req.get("feature", "Requirement"))
    req["scenario"] = _clean(req.get("scenario", req["feature"]))
    req["actions"] = _clean(req.get("actions", "Load page and perform the stated user action where applicable."))
    req["expected"] = _clean(req.get("expected", req["scenario"]))
    req["endpoint"] = _infer_endpoint(" ".join([req["feature"], req["scenario"], req["actions"], req["expected"]]))
    req["base_url"] = BASE_URL
    return req


def extract_requirements(pdf_path: str) -> List[Dict[str, str]]:
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        return []

    lines = [_clean(line) for line in text.splitlines() if _clean(line)]
    requirements: List[Dict[str, str]] = []

    for idx, line in enumerate(lines):
        match = re.match(r"^(FR-[A-Z0-9-]+)\s*[–-]\s*(.+)$", line)
        if not match:
            continue
        req_id, title = match.groups()
        block = _block_until_next(lines, idx)
        description = _extract_field(block, "Description")
        expected = _extract_field(block, "Expected(?: System)? Behavior") or _extract_field(block, "Expected Behavior")
        actions = _extract_field(block, "User Actions")
        requirements.append(_normalize_requirement({
            "id": req_id,
            "feature": title,
            "scenario": description or title,
            "actions": actions,
            "expected": expected or description or title,
            "source": "SRS PDF formal block",
        }))

    # Concise bullets: "FR-AB-01: The page shall..."
    for line in lines:
        match = re.search(r"\b(FR-[A-Z0-9-]+)\s*:\s*(.+?)(?:$|\s*\s*)", line, flags=re.I)
        if not match:
            continue
        req_id, sentence = match.groups()
        if not re.search(r"\bshall\b", sentence, flags=re.I):
            continue
        if any(r["id"] == req_id for r in requirements):
            continue
        requirements.append(_normalize_requirement({
            "id": req_id,
            "feature": sentence[:90],
            "scenario": sentence,
            "actions": "Load page and perform the stated interaction when applicable.",
            "expected": sentence,
            "source": "SRS PDF concise requirement",
        }))

    # Stable ordering and de-duplication.
    seen = set()
    unique: List[Dict[str, str]] = []
    for req in requirements:
        key = req.get("id") or (req.get("endpoint"), req.get("feature"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(req)
    return unique
