"""Agent C: validate generated Playwright code for hallucinations and coverage."""
from __future__ import annotations

import re
from typing import Dict, List

KNOWN_PATHS = {
    '/', '/checkboxes', '/login', '/dropdown', '/dynamic_controls', '/dynamic_loading', '/upload',
    '/javascript_alerts', '/drag_and_drop', '/tables', '/notification_message_rendered', '/entry_ad',
    '/typos', '/add_remove_elements/', '/disappearing_elements', '/hovers', '/abtest', '/dynamic_content',
    '/status_codes', '/inputs', '/horizontal_slider', '/context_menu', '/challenging_dom', '/exit_intent',
    '/jqueryui/menu', '/javascript_error', '/large', '/infinite_scroll', '/download', '/forgot_password',
    '/geolocation', '/floating_menu', '/shadowdom', '/frames', '/windows', '/shifting_content'
}

REQUIRED_LOCATORS = {
    '/login': ['#username', '#password'],
    '/dropdown': ['#dropdown'],
    '/checkboxes': ['input[type=checkbox]'],
    '/upload': ['input[type=file]'],
    '/javascript_alerts': ['Click for JS Alert'],
    '/tables': ['table'],
    '/add_remove_elements/': ['Add Element'],
    '/hovers': ['.figure'],
    '/context_menu': ['#hot-spot'],
    '/horizontal_slider': ['input[type=range]'],
}


def _issues(requirement: Dict[str, str], script: str) -> List[str]:
    issues: List[str] = []
    path = requirement.get('endpoint') or '/'
    if "import { test, expect } from '@playwright/test'" not in script:
        issues.append('Missing Playwright test/expect import.')
    if 'test(' not in script:
        issues.append('Missing Playwright test block.')
    if 'page.goto' not in script:
        issues.append('Script does not navigate to the requirement page.')
    if 'expect(' not in script:
        issues.append('Script has no assertions.')
    if path not in script:
        issues.append(f'Script does not target expected endpoint {path}.')
    if path not in KNOWN_PATHS:
        issues.append(f'Possible hallucinated endpoint: {path}.')
    for locator in REQUIRED_LOCATORS.get(path, []):
        if locator not in script:
            issues.append(f'Missing expected stable locator/text for {path}: {locator}.')
    if re.search(r'page\.locator\(["\']#[a-zA-Z0-9_-]{12,}', script):
        issues.append('Suspicious generated dynamic id locator; use stable locators.')
    if 'setTimeout' in script or 'waitForTimeout' in script:
        issues.append('Avoid fixed sleeps; use Playwright auto-waiting assertions.')
    if re.search(r"toContainText\(\s*['\"]\s*(?:The page shall|Display a list of|Provide a|Allow the user|Grant access|Display error messages)", script, re.I):
        issues.append('Assertion appears to use requirement prose instead of actual UI text; assert observable UI labels/headings/locators only.')
    if re.search(r"getByText\(\s*['\"]\s*(?:The page shall|Display a list of|Provide a|Allow the user)", script, re.I):
        issues.append('Text assertion appears to use SRS prose instead of rendered website text.')
    if len(script.strip()) < 120:
        issues.append('Script is too short to cover the requirement.')
    return issues


def validate_script(requirement: Dict[str, str], script: str) -> str:
    issues = _issues(requirement if isinstance(requirement, dict) else {}, script)
    if issues:
        return 'FAIL: ' + ' '.join(issues)
    return 'PASS: Script uses a valid endpoint, stable locators, Playwright assertions, and covers the requirement without obvious hallucinations.'
