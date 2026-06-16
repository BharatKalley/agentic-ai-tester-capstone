"""Agent A: extract atomic, testable FR and NFR requirements from an SRS PDF."""
from __future__ import annotations

import os
import re
from typing import Dict, List

from parser.pdf_parser import extract_text_from_pdf

BASE_URL = os.getenv("BASE_URL", "https://the-internet.herokuapp.com")
REQ_ID_RE = r"(?:FR|NFR)-[A-Z0-9-]+"
FIELD_NAMES = (
    r"Feature Name|Description|Preconditions|User Actions|"
    r"Expected (?:System )?Behavior|Expected Behavior|Validation|Source text|"
    rf"{REQ_ID_RE}|\d+\.\d+(?:\.\d+)?"
)

ADD_REMOVE_PATH = "/add_remove_elements/"
LOGIN_PATH = "/login"
DYNAMIC_CONTROLS_PATH = "/dynamic_controls"
DYNAMIC_LOADING_PATH = "/dynamic_loading"
DYNAMIC_CONTENT_PATH = "/dynamic_content"
UPLOAD_PATH = "/upload"
DOWNLOAD_PATH = "/download"
JS_ALERTS_PATH = "/javascript_alerts"
JS_ERROR_PATH = "/javascript_error"
DRAG_DROP_PATH = "/drag_and_drop"
TABLES_PATH = "/tables"
CHECKBOXES_PATH = "/checkboxes"
ROOT_PATH = "/"

PATH_BY_KEYWORD = [
    ("add/remove", ADD_REMOVE_PATH), ("add remove", ADD_REMOVE_PATH),
    ("form authentication", LOGIN_PATH), ("valid credentials", LOGIN_PATH), ("invalid credentials", LOGIN_PATH),
    ("dynamic controls", DYNAMIC_CONTROLS_PATH), ("dynamic loading", DYNAMIC_LOADING_PATH), ("dynamic content", DYNAMIC_CONTENT_PATH),
    ("file uploader", UPLOAD_PATH), ("file upload", UPLOAD_PATH), ("file downloader", DOWNLOAD_PATH), ("file download", DOWNLOAD_PATH),
    ("javascript alerts", JS_ALERTS_PATH), ("js alert", JS_ALERTS_PATH), ("js confirm", JS_ALERTS_PATH), ("js prompt", JS_ALERTS_PATH),
    ("javascript error", JS_ERROR_PATH), ("drag and drop", DRAG_DROP_PATH),
    ("sortable data tables", TABLES_PATH), ("data tables", TABLES_PATH),
    ("notification message", "/notification_message_rendered"), ("entry ad", "/entry_ad"), ("disappearing elements", "/disappearing_elements"),
    ("horizontal slider", "/horizontal_slider"), ("context menu", "/context_menu"), ("challenging dom", "/challenging_dom"), ("exit intent", "/exit_intent"),
    ("jquery ui", "/jqueryui/menu"), ("jquery", "/jqueryui/menu"), ("infinite scroll", "/infinite_scroll"), ("forgot password", "/forgot_password"),
    ("floating menu", "/floating_menu"), ("shadow dom", "/shadowdom"), ("shifting content", "/shifting_content"), ("status codes", "/status_codes"),
    ("checkbox", CHECKBOXES_PATH), ("dropdown", "/dropdown"), ("upload", UPLOAD_PATH), ("alert", JS_ALERTS_PATH), ("tables", TABLES_PATH),
    ("typos", "/typos"), ("hovers", "/hovers"), ("a/b", "/abtest"), ("inputs", "/inputs"), ("large", "/large"),
    ("geolocation", "/geolocation"), ("frames", "/frames"), ("windows", "/windows"),
    ("home page", ROOT_PATH), ("root url", ROOT_PATH), ("footer", CHECKBOXES_PATH),
]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip(" •o:-\t")


def _infer_endpoint(text: str) -> str:
    lower = text.lower()
    explicit = [p for p in re.findall(r"(?<!\w)(/[a-zA-Z0-9_/-]+)(?!\w)", text) if p not in {"/", "//"}]
    if explicit:
        return explicit[0]
    if "welcome to the-internet" in lower or "root url" in lower:
        return ROOT_PATH
    return next((path for key, path in PATH_BY_KEYWORD if key in lower), "/")


def _req_type(req_id: str) -> str:
    return "non_functional" if req_id.upper().startswith("NFR-") else "functional"


def _block_until_next(lines: List[str], start: int) -> str:
    next_req = rf"^{REQ_ID_RE}\s*[–:-]"
    next_heading = r"^\d+\.\d+(?:\.\d+)?\s+"
    end = next((i for i in range(start + 1, len(lines)) if re.match(next_req, lines[i], re.I) or re.match(next_heading, lines[i])), len(lines))
    return "\n".join(lines[start:end])


def _extract_field(block: str, label: str) -> str:
    match = re.search(rf"{label}\s*:?[\s\n]*(.*?)(?=\n\s*(?:{FIELD_NAMES})|\Z)", block, flags=re.I | re.S)
    return _clean(match.group(1)) if match else ""


def _normalize(req: Dict[str, str]) -> Dict[str, str]:
    req["feature"] = _clean(req.get("feature", "Requirement"))
    req["scenario"] = _clean(req.get("scenario", req["feature"]))
    req["actions"] = _clean(req.get("actions", "Load page and perform the stated user action where applicable."))
    req["expected"] = _clean(req.get("expected", req["scenario"]))
    req["type"] = req.get("type") or _req_type(req.get("id", "FR"))
    req["endpoint"] = _infer_endpoint(" ".join(req.get(k, "") for k in ("feature", "scenario", "actions", "expected")))
    req["base_url"] = BASE_URL
    return req


def _formal_requirements(lines: List[str]) -> List[Dict[str, str]]:
    requirements = []
    for idx, line in enumerate(lines):
        match = re.match(rf"^({REQ_ID_RE})\s*[–-]\s*(.+)$", line, flags=re.I)
        if not match:
            continue
        req_id, title = match.groups()
        block = _block_until_next(lines, idx)
        desc = _extract_field(block, "Description")
        expected = _extract_field(block, "Expected(?: System)? Behavior") or _extract_field(block, "Expected Behavior")
        requirements.append(_normalize({
            "id": req_id.upper(), "type": _req_type(req_id), "feature": title, "scenario": desc or title,
            "actions": _extract_field(block, "User Actions"), "expected": expected or desc or title,
            "source": "SRS PDF formal block",
        }))
    return requirements


def _concise_requirements(lines: List[str], existing_ids: set[str]) -> List[Dict[str, str]]:
    found = []
    for line in lines:
        # Handles: FR-AB-01: The page shall... and NFR-U-01: Page structures shall...
        match = re.search(rf"\b({REQ_ID_RE})\s*:\s*(.+?)(?:$|\s*\s*)", line, flags=re.I)
        if not match:
            continue
        req_id, sentence = match.groups()
        req_id = req_id.upper()
        if req_id in existing_ids or not re.search(r"\b(shall|should|must)\b", sentence, flags=re.I):
            continue
        found.append(_normalize({
            "id": req_id, "type": _req_type(req_id), "feature": sentence[:90], "scenario": sentence,
            "actions": "Load page and verify the stated quality or behavior where applicable.",
            "expected": sentence, "source": "SRS PDF concise requirement",
        }))
    return found


def extract_requirements(pdf_path: str) -> List[Dict[str, str]]:
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        return []

    lines = [_clean(line) for line in text.splitlines() if _clean(line)]
    requirements = _formal_requirements(lines)
    requirements += _concise_requirements(lines, {r["id"] for r in requirements})

    seen, unique = set(), []
    for req in requirements:
        key = req.get("id") or (req.get("endpoint"), req.get("feature"))
        if key not in seen:
            seen.add(key)
            unique.append(req)
    return unique
