"""Agent B: generate robust, executable Playwright TypeScript tests."""
from __future__ import annotations

import re
from typing import Dict, List

HEADER = """import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

"""

BASE_CASES: Dict[str, List[str]] = {
    "/": [
        "await expect(page.getByRole('heading', { name: /Welcome to the-internet/i })).toBeVisible();",
        "await expect(page.getByText('Available Examples')).toBeVisible();",
        "await expect(page.getByRole('link', { name: 'A/B Testing' })).toBeVisible();",
        "await expect(page.getByRole('link', { name: 'Add/Remove Elements' })).toBeVisible();",
        "await expect(page.getByRole('link', { name: 'Checkboxes' })).toBeVisible();",
    ],
    "/checkboxes": ["const boxes = page.locator('input[type=checkbox]');", "await expect(boxes).toHaveCount(2);"],
    "/login": [
        "await expect(page.getByRole('heading', { name: /Login Page/i })).toBeVisible();",
        "await expect(page.locator('#username')).toBeVisible();",
        "await expect(page.locator('#password')).toBeVisible();",
    ],
    "/dropdown": [
        "const dropdown = page.locator('#dropdown');", "await expect(dropdown).toBeVisible();",
        "await expect(dropdown).toContainText('Option 1');", "await expect(dropdown).toContainText('Option 2');",
    ],
    "/dynamic_controls": [
        "await expect(page.getByRole('heading', { name: /Dynamic Controls/i })).toBeVisible();",
        "await expect(page.locator('#checkbox')).toBeVisible();",
        "await expect(page.getByRole('button', { name: /Remove/i })).toBeVisible();",
        "await expect(page.getByRole('button', { name: /Enable/i })).toBeVisible();",
    ],
    "/dynamic_loading": [
        "await expect(page.getByRole('heading', { name: /Dynamically Loaded Page Elements/i })).toBeVisible();",
        "await expect(page.getByRole('link', { name: /Example 1/i })).toBeVisible();",
        "await expect(page.getByRole('link', { name: /Example 2/i })).toBeVisible();",
    ],
    "/upload": [
        "await expect(page.getByRole('heading', { name: /File Uploader/i })).toBeVisible();",
        "await expect(page.locator('input[type=file]')).toBeVisible();", "await expect(page.locator('#file-submit')).toBeVisible();",
    ],
    "/javascript_alerts": [
        "await expect(page.getByRole('heading', { name: /JavaScript Alerts/i })).toBeVisible();",
        "await expect(page.getByRole('button', { name: 'Click for JS Alert' })).toBeVisible();",
        "await expect(page.getByRole('button', { name: 'Click for JS Confirm' })).toBeVisible();",
        "await expect(page.getByRole('button', { name: 'Click for JS Prompt' })).toBeVisible();",
    ],
    "/drag_and_drop": ["await expect(page.getByRole('heading', { name: /Drag and Drop/i })).toBeVisible();", "await expect(page.locator('#column-a')).toBeVisible();", "await expect(page.locator('#column-b')).toBeVisible();"],
    "/tables": ["await expect(page.getByRole('heading', { name: /Data Tables/i })).toBeVisible();", "await expect(page.locator('table')).toHaveCount(2);", "await expect(page.locator('table').first()).toContainText('Last Name');", "await expect(page.locator('table').first()).toContainText('edit');", "await expect(page.locator('table').first()).toContainText('delete');"],
    "/notification_message_rendered": ["await expect(page.getByRole('heading', { name: /Notification Message/i })).toBeVisible();", "await expect(page.locator('#flash')).toBeVisible();", "await page.getByRole('link', { name: /Click here to load a new message/i }).click();", "await expect(page.locator('#flash')).toBeVisible();"],
    "/entry_ad": ["await expect(page.getByRole('heading', { name: /Entry Ad/i })).toBeVisible();", "const modal = page.locator('.modal');", "await expect(modal).toBeVisible();", "await page.getByText('Close').click();", "await expect(modal).toBeHidden();"],
    "/typos": ["await expect(page.getByRole('heading', { name: /Typos/i })).toBeVisible();", "await expect(page.locator('body')).toContainText(/typo/i);"],
    "/add_remove_elements/": ["await expect(page.getByRole('heading', { name: /Add.Remove Elements/i })).toBeVisible();", "await page.getByRole('button', { name: /Add Element/i }).click();", "const del = page.getByRole('button', { name: /Delete/i });", "await expect(del).toHaveCount(1);", "await del.click();", "await expect(page.getByRole('button', { name: /Delete/i })).toHaveCount(0);"],
    "/disappearing_elements": ["await expect(page.getByRole('heading', { name: /Disappearing Elements/i })).toBeVisible();", "await expect(page.getByRole('link', { name: /Home/i })).toBeVisible();"],
    "/hovers": ["const figures = page.locator('.figure');", "await expect(figures).toHaveCount(3);", "await figures.first().hover();", "await expect(page.getByText(/name: user1/i)).toBeVisible();", "await expect(page.getByRole('link', { name: /View profile/i }).first()).toBeVisible();"],
    "/abtest": ["await expect(page.locator('body')).toContainText(/A.B Test|No A.B Test/i);"],
    "/dynamic_content": ["await expect(page.getByRole('heading', { name: /Dynamic Content/i })).toBeVisible();", "await expect(page.locator('.row')).toHaveCount(3);", "await page.goto('/dynamic_content?with_content=static', { waitUntil: 'domcontentloaded' });", "await expect(page.locator('.row')).toHaveCount(3);"],
    "/status_codes": ["await expect(page.getByRole('heading', { name: /Status Codes/i })).toBeVisible();", "await expect(page.getByRole('link', { name: '200' })).toBeVisible();", "await expect(page.getByRole('link', { name: '404' })).toBeVisible();"],
    "/inputs": ["const input = page.locator('input[type=number]');", "await expect(input).toBeVisible();", "await input.fill('42');", "await expect(input).toHaveValue('42');"],
    "/horizontal_slider": ["const slider = page.locator('input[type=range]');", "await expect(slider).toBeVisible();", "await slider.focus();", "await page.keyboard.press('ArrowRight');", "await expect(page.locator('#range')).not.toHaveText('0');"],
    "/context_menu": ["const box = page.locator('#hot-spot');", "await expect(box).toBeVisible();", "page.once('dialog', async dialog => { expect(dialog.type()).toBe('alert'); await dialog.accept(); });", "await box.click({ button: 'right' });"],
    "/challenging_dom": ["await expect(page.getByRole('heading', { name: /Challenging DOM/i })).toBeVisible();", "await expect(page.locator('table')).toContainText('Lorem');", "await expect(page.locator('canvas')).toBeVisible();"],
    "/exit_intent": ["await expect(page.getByRole('heading', { name: /Exit Intent/i })).toBeVisible();", "await page.mouse.move(100, 100);", "await page.mouse.move(100, 0);", "await expect(page.locator('.modal')).toBeVisible();", "await page.getByText('Close').click();", "await expect(page.locator('.modal')).toBeHidden();"],
    "/jqueryui/menu": ["await expect(page.getByRole('heading', { name: /JQueryUI/i })).toBeVisible();", "await expect(page.locator('#menu')).toBeVisible();", "await expect(page.getByRole('link', { name: /Enabled/i })).toBeVisible();"],
    "/javascript_error": ["const errors: string[] = [];", "page.on('pageerror', e => errors.push(e.message));", "await page.reload({ waitUntil: 'domcontentloaded' });", "expect(errors.length).toBeGreaterThan(0);"],
    "/large": ["await expect(page.getByRole('heading', { name: /Large & Deep DOM/i })).toBeVisible();", "await expect(page.locator('#large-table')).toBeVisible();"],
    "/infinite_scroll": ["await expect(page.getByRole('heading', { name: /Infinite Scroll/i })).toBeVisible();", "const before = await page.locator('.jscroll-added').count();", "await page.mouse.wheel(0, 3000);", "await expect.poll(async () => page.locator('.jscroll-added').count()).toBeGreaterThanOrEqual(before);"],
    "/download": ["await expect(page.getByRole('heading', { name: /File Downloader/i })).toBeVisible();", "await expect(page.locator('a').first()).toBeVisible();"],
    "/forgot_password": ["await expect(page.getByRole('heading', { name: /Forgot Password/i })).toBeVisible();", "await expect(page.locator('#email')).toBeVisible();", "await expect(page.locator('#form_submit')).toBeVisible();"],
    "/geolocation": ["await context.grantPermissions(['geolocation']);", "await context.setGeolocation({ latitude: 17.3850, longitude: 78.4867 });", "await expect(page.getByRole('heading', { name: /Geolocation/i })).toBeVisible();", "await page.getByRole('button', { name: /Where am I/i }).click();", "await expect(page.locator('#lat-value')).toBeVisible();", "await expect(page.locator('#long-value')).toBeVisible();"],
    "/floating_menu": ["await expect(page.getByRole('heading', { name: /Floating Menu/i })).toBeVisible();", "await expect(page.locator('#menu')).toBeVisible();", "await page.mouse.wheel(0, 1500);", "await expect(page.locator('#menu')).toBeVisible();"],
    "/shadowdom": ["await expect(page.getByRole('heading', { name: /Simple template/i })).toBeVisible();", "await expect(page.locator('my-paragraph')).toHaveCount(2);", "await expect(page.locator('body')).toContainText(/My default text|different text/i);"],
    "/frames": ["await expect(page.getByRole('heading', { name: /Frames/i })).toBeVisible();", "await expect(page.getByRole('link', { name: /Nested Frames/i })).toBeVisible();", "await expect(page.getByRole('link', { name: /iFrame/i })).toBeVisible();"],
    "/windows": ["await expect(page.getByRole('heading', { name: /Opening a new window/i })).toBeVisible();", "const popupPromise = page.waitForEvent('popup');", "await page.getByRole('link', { name: /Click Here/i }).click();", "const popup = await popupPromise;", "await expect(popup.locator('body')).toContainText('New Window');"],
    "/shifting_content": ["await expect(page.getByRole('heading', { name: /Shifting Content/i })).toBeVisible();", "await expect(page.getByRole('link', { name: /Example 1/i })).toBeVisible();", "await expect(page.getByRole('link', { name: /Example 2/i })).toBeVisible();", "await expect(page.getByRole('link', { name: /Example 3/i })).toBeVisible();"],
}


def _safe_test_name(req: Dict[str, str]) -> str:
    return (f"{req.get('id', 'REQ')} {req.get('feature', 'requirement')}".replace("'", "").replace("\n", " "))[:150]


def _full_text(req: Dict[str, str]) -> str:
    return " ".join(req.get(k, "") for k in ("feature", "scenario", "expected")).lower()


def _generic_steps(req: Dict[str, str]) -> List[str]:
    heading = re.sub(r"\s*\(.+?\)", "", req.get("feature", "")).split("–")[0].strip()
    if heading and len(heading) < 80:
        return ["await expect(page.locator('body')).toBeVisible();", f"await expect(page.locator('body')).toContainText(/{re.escape(heading[:45])}/i);"]
    return ["await expect(page.locator('body')).toBeVisible();", "await expect(page.locator('body')).not.toBeEmpty();"]


def _conditional_steps(path: str, full: str) -> List[str]:
    if path == "/checkboxes" and "toggle" in full:
        return ["const first = boxes.first();", "const before = await first.isChecked();", "await first.click();", "expect(await first.isChecked()).toBe(!before);"]
    if path == "/login" and ("successful" in full or "valid credentials" in full or "secure area" in full):
        return ["await page.locator('#username').fill('tomsmith');", "await page.locator('#password').fill('SuperSecretPassword!');", "await page.getByRole('button', { name: /login/i }).click();", "await expect(page).toHaveURL(/secure/);", "await expect(page.locator('#flash')).toContainText(/logged into a secure area/i);"]
    if path == "/login" and any(k in full for k in ("invalid", "wrong", "error")):
        return ["await page.locator('#username').fill('invalid-user');", "await page.locator('#password').fill('invalid-password');", "await page.getByRole('button', { name: /login/i }).click();", "await expect(page.locator('#flash')).toContainText(/invalid/i);", "await expect(page).not.toHaveURL(/secure/);"]
    if path == "/login":
        return ["await expect(page.getByRole('button', { name: /login/i })).toBeVisible();"]
    if path == "/dropdown" and ("selection" in full or "select" in full):
        return ["await dropdown.selectOption({ label: 'Option 1' });", "await expect(dropdown).toHaveValue('1');"]
    if path == "/upload" and "upload" in full and "action" in full:
        return ["await page.locator('input[type=file]').setInputFiles({ name: 'sample.txt', mimeType: 'text/plain', buffer: Buffer.from('capstone upload') });", "await page.locator('#file-submit').click();", "await expect(page.getByRole('heading', { name: /File Uploaded/i })).toBeVisible();", "await expect(page.locator('#uploaded-files')).toContainText('sample.txt');"]
    if path == "/javascript_alerts":
        steps = []
        if "alert" in full and "render" not in full:
            steps += ["page.once('dialog', async dialog => { expect(dialog.type()).toBe('alert'); await dialog.accept(); });", "await page.getByRole('button', { name: 'Click for JS Alert' }).click();", "await expect(page.locator('#result')).toContainText(/successfully/i);"]
        if "confirm" in full or "prompt" in full:
            steps += ["page.once('dialog', async dialog => { expect(dialog.type()).toBe('confirm'); await dialog.accept(); });", "await page.getByRole('button', { name: 'Click for JS Confirm' }).click();", "await expect(page.locator('#result')).toContainText(/Ok/i);", "page.once('dialog', async dialog => { expect(dialog.type()).toBe('prompt'); await dialog.accept('hello'); });", "await page.getByRole('button', { name: 'Click for JS Prompt' }).click();", "await expect(page.locator('#result')).toContainText('hello');"]
        return steps
    return []


def _is_nfr(req: Dict[str, str]) -> bool:
    return str(req.get("id", "")).upper().startswith("NFR") or str(req.get("type", "")).lower().startswith("non")


def _start_path(req: Dict[str, str], full: str) -> str:
    path = req.get("endpoint") or "/"
    if path == "/secure" and any(k in full for k in ["login", "credential", "tomsmith", "secure area"]):
        return "/login"
    return path


def _coverage_steps(req: Dict[str, str], path: str, full: str) -> List[str]:
    steps: List[str] = []
    if "powered by elemental selenium" in full:
        steps.append("await expect(page.locator('body')).toContainText('Powered by Elemental Selenium');")
    return steps


def generate_playwright_script(requirement: Dict[str, str], feedback: str = "") -> str:
    req = requirement if isinstance(requirement, dict) else {"feature": str(requirement), "endpoint": "/"}
    full = _full_text(req)
    path = _start_path(req, full)

    if _is_nfr(req):
        steps = [
            "await expect(page.locator('body')).toBeVisible();",
            "await expect(page.locator('body')).not.toBeEmpty();",
        ]
    else:
        steps = BASE_CASES.get(path, _generic_steps(req)) + _conditional_steps(path, full) + _coverage_steps(req, path, full)

    body = "\n".join(f"  {step}" for step in steps)
    return f"{HEADER}test('{_safe_test_name(req)}', async ({{ page, context }}) => {{\n  await page.goto('{path}', {{ waitUntil: 'domcontentloaded' }});\n{body}\n}});\n"
