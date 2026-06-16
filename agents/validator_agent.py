"""Agent C: validate generated Playwright code for hallucinations and requirement coverage."""
from __future__ import annotations

import re
from typing import Dict, List

KNOWN_PATHS = {
    '/', '/checkboxes', '/login', '/secure', '/dropdown', '/dynamic_controls', '/dynamic_loading', '/upload',
    '/javascript_alerts', '/drag_and_drop', '/tables', '/notification_message_rendered', '/entry_ad',
    '/typos', '/add_remove_elements/', '/disappearing_elements', '/hovers', '/abtest', '/dynamic_content',
    '/status_codes', '/inputs', '/horizontal_slider', '/context_menu', '/challenging_dom', '/exit_intent',
    '/jqueryui/menu', '/javascript_error', '/large', '/infinite_scroll', '/download', '/forgot_password',
    '/geolocation', '/floating_menu', '/shadowdom', '/frames', '/windows', '/shifting_content'
}

REQUIRED_LOCATORS = {
    '/login': ['#username', '#password'], '/dropdown': ['#dropdown'], '/checkboxes': ['input[type=checkbox]'],
    '/upload': ['input[type=file]'], '/javascript_alerts': ['Click for JS Alert'], '/tables': ['table'],
    '/add_remove_elements/': ['Add Element'], '/hovers': ['.figure'], '/context_menu': ['#hot-spot'],
    '/horizontal_slider': ['input[type=range]'],
}

BAD_PROSE = r"(?:The page shall|Display a list of|Provide a|Allow the user|Grant access|Display error messages)"


def _text(req: Dict[str, str]) -> str:
    return " ".join(str(req.get(k, "")) for k in ("id", "type", "feature", "scenario", "actions", "expected")).lower()


def _is_nfr(req: Dict[str, str]) -> bool:
    return str(req.get("id", "")).upper().startswith("NFR") or str(req.get("type", "")).lower().startswith("non")


def _target_path(req: Dict[str, str]) -> str:
    """Return the page where the test should start.

    /secure is a post-login destination. A successful-login test must start at /login,
    then assert navigation to /secure.
    """
    path, text = req.get("endpoint") or "/", _text(req)
    if path == "/secure" and any(k in text for k in ["login", "credential", "tomsmith", "secure area"]):
        return "/login"
    return path


def _requirement_coverage_issues(req: Dict[str, str], script: str) -> List[str]:
    text, s = _text(req), script.lower()
    issues: List[str] = []

    if "powered by elemental selenium" in text and "powered by elemental selenium" not in s:
        issues.append('Requirement not covered: footer text "Powered by Elemental Selenium" is not asserted.')
    if any(k in text for k in ["successful login", "valid credentials", "tomsmith", "secure area"]):
        for needed in ["#username", "#password", "tomsmith", "supersecretpassword!", "tohaveurl(/secure", "logged into a secure area"]:
            if needed not in s:
                issues.append(f"Requirement not covered: successful login step/assertion missing: {needed}.")
    if any(k in text for k in ["invalid credentials", "wrong", "incorrect", "error message"]):
        if "invalid" not in s or "not.tohaveurl(/secure" not in s:
            issues.append("Requirement not covered: invalid login error and secure-area blocking are not asserted.")
    if "toggle" in text and not all(x in s for x in [".click(", "ischecked"]):
        issues.append("Requirement not covered: checkbox toggle state change is not asserted.")
    if "option selection" in text or "select an option" in text:
        if "selectoption" not in s or "tohavevalue" not in s:
            issues.append("Requirement not covered: dropdown selection and resulting value are not asserted.")
    if "upload action" in text or "file has been uploaded" in text:
        if "setinputfiles" not in s or "file uploaded" not in s or "uploaded-files" not in s:
            issues.append("Requirement not covered: file upload action and confirmation are not asserted.")
    if "js alert" in text and "rendering" not in text and "dialog" not in s:
        issues.append("Requirement not covered: JavaScript dialog handling is missing.")
    return issues


def _issues(requirement: Dict[str, str], script: str) -> List[str]:
    req = requirement if isinstance(requirement, dict) else {}
    path, target = req.get('endpoint') or '/', _target_path(req)
    if _is_nfr(req):
        return []  # NFRs are handled as manual-review/passive checks by orchestrator.

    checks = [
        ("import { test, expect } from '@playwright/test'" in script, 'Missing Playwright test/expect import.'),
        ('test(' in script, 'Missing Playwright test block.'),
        ('page.goto' in script, 'Script does not navigate to the requirement page.'),
        ('expect(' in script, 'Script has no assertions.'),
        (target in script, f'Script does not target expected start endpoint {target}.'),
        (path in KNOWN_PATHS, f'Possible hallucinated endpoint: {path}.'),
        (target in KNOWN_PATHS, f'Possible hallucinated start endpoint: {target}.'),
        (not re.search(r'page\.locator\(["\']#[a-zA-Z0-9_-]{12,}', script), 'Suspicious generated dynamic id locator; use stable locators.'),
        ('setTimeout' not in script and 'waitForTimeout' not in script, 'Avoid fixed sleeps; use Playwright auto-waiting assertions.'),
        (not re.search(rf"toContainText\(\s*['\"]\s*{BAD_PROSE}", script, re.I), 'Assertion appears to use requirement prose instead of actual UI text.'),
        (not re.search(rf"getByText\(\s*['\"]\s*{BAD_PROSE}", script, re.I), 'Text assertion appears to use SRS prose instead of rendered website text.'),
        (len(script.strip()) >= 120, 'Script is too short to cover the requirement.'),
    ]
    issues = [msg for ok, msg in checks if not ok]
    issues += [f'Missing expected stable locator/text for {target}: {loc}.' for loc in REQUIRED_LOCATORS.get(target, []) if loc.lower() not in script.lower()]
    issues += _requirement_coverage_issues(req, script)
    return issues


def validate_script(requirement: Dict[str, str], script: str) -> str:
    req = requirement if isinstance(requirement, dict) else {}
    if _is_nfr(req):
        return 'PASS_NFR_REVIEW: Non-functional requirement extracted. Browser execution is skipped; review through coverage/report evidence.'
    issues = _issues(req, script)
    return 'FAIL: ' + ' '.join(issues) if issues else 'PASS: Script uses a valid endpoint, stable locators, Playwright assertions, and covers the requirement.'
