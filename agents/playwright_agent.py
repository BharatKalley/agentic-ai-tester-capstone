"Agent B: generate robust, executable Playwright TypeScript tests."
from __future__ import annotations

import re
from typing import Dict, List

ROOT_PATH, LOGIN_PATH, CHECKBOXES_PATH = "/", "/login", "/checkboxes"
DROPDOWN_PATH, UPLOAD_PATH = "/dropdown", "/upload"
JS_ALERTS_PATH, SECURE_PATH = "/javascript_alerts", "/secure"
BODY = "await expect(page.locator('body'))"
BODY_VISIBLE_STEP = f"{BODY}.toBeVisible();"
BODY_NOT_EMPTY_STEP = f"{BODY}.not.toBeEmpty();"
MENU_VISIBLE_STEP = "await expect(page.locator('#menu')).toBeVisible();"
FOOTER_TEXT = "powered by elemental selenium"

HEADER = """import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

"""


def _ts_quote(text: str) -> str:
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _h(text: str) -> str:
    return f"await expect(page.getByRole('heading', {{ name: {_ts_quote(text)} }})).toBeVisible();"


def _link(text: str) -> str:
    return f"await expect(page.getByRole('link', {{ name: {_ts_quote(text)} }})).toBeVisible();"


BASE_CASES: Dict[str, List[str]] = {
    ROOT_PATH: [_h("Welcome to the-internet"), "await expect(page.getByText('Available Examples')).toBeVisible();", _link("A/B Testing"), _link("Add/Remove Elements"), _link("Checkboxes")],
    CHECKBOXES_PATH: ["const boxes = page.locator('input[type=checkbox]');", "await expect(boxes).toHaveCount(2);"],
    LOGIN_PATH: [_h("Login Page"), "await expect(page.locator('#username')).toBeVisible();", "await expect(page.locator('#password')).toBeVisible();"],
    DROPDOWN_PATH: ["const dropdown = page.locator('#dropdown');", "await expect(dropdown).toBeVisible();", "await expect(dropdown).toContainText('Option 1');", "await expect(dropdown).toContainText('Option 2');"],
    "/dynamic_controls": [_h("Dynamic Controls"), "await expect(page.locator('#checkbox')).toBeVisible();", "await expect(page.getByRole('button', { name: /Remove/i })).toBeVisible();", "await expect(page.getByRole('button', { name: /Enable/i })).toBeVisible();"],
    "/dynamic_loading": [_h("Dynamically Loaded Page Elements"), _link("Example 1"), _link("Example 2")],
    UPLOAD_PATH: [_h("File Uploader"), "await expect(page.locator('input[type=file]')).toBeVisible();", "await expect(page.locator('#file-submit')).toBeVisible();"],
    JS_ALERTS_PATH: [_h("JavaScript Alerts"), "await expect(page.getByRole('button', { name: 'Click for JS Alert' })).toBeVisible();", "await expect(page.getByRole('button', { name: 'Click for JS Confirm' })).toBeVisible();", "await expect(page.getByRole('button', { name: 'Click for JS Prompt' })).toBeVisible();"],
    "/drag_and_drop": [_h("Drag and Drop"), "await expect(page.locator('#column-a')).toBeVisible();", "await expect(page.locator('#column-b')).toBeVisible();"],
    "/tables": [_h("Data Tables"), "await expect(page.locator('table')).toHaveCount(2);", "await expect(page.locator('table').first()).toContainText('Last Name');", "await expect(page.locator('table').first()).toContainText('edit');", "await expect(page.locator('table').first()).toContainText('delete');"],
    "/notification_message_rendered": [_h("Notification Message"), "await expect(page.locator('#flash')).toBeVisible();", "await page.getByRole('link', { name: /Click here to load a new message/i }).click();", "await expect(page.locator('#flash')).toBeVisible();"],
    "/entry_ad": [_h("Entry Ad"), "const modal = page.locator('.modal');", "await expect(modal).toBeVisible();", "await page.getByText('Close').click();", "await expect(modal).toBeHidden();"],
    "/typos": [_h("Typos"), "await expect(page.locator('body')).toContainText(/typo/i);"],
    "/add_remove_elements/": [_h("Add.Remove Elements"), "await page.getByRole('button', { name: /Add Element/i }).click();", "const del = page.getByRole('button', { name: /Delete/i });", "await expect(del).toHaveCount(1);", "await del.click();", "await expect(page.getByRole('button', { name: /Delete/i })).toHaveCount(0);"],
    "/disappearing_elements": [_h("Disappearing Elements"), _link("Home")],
    "/hovers": ["const figures = page.locator('.figure');", "await expect(figures).toHaveCount(3);", "await figures.first().hover();", "await expect(page.getByText(/name: user1/i)).toBeVisible();", "await expect(page.getByRole('link', { name: /View profile/i }).first()).toBeVisible();"],
    "/abtest": ["await expect(page.locator('body')).toContainText(/A.B Test|No A.B Test/i);"],
    "/dynamic_content": [_h("Dynamic Content"), "await expect(page.locator('.row')).toHaveCount(3);", "await page.goto('/dynamic_content?with_content=static', { waitUntil: 'domcontentloaded' });", "await expect(page.locator('.row')).toHaveCount(3);"],
    "/status_codes": [_h("Status Codes"), "await expect(page.getByRole('link', { name: '200' })).toBeVisible();", "await expect(page.getByRole('link', { name: '404' })).toBeVisible();"],
    "/inputs": ["const input = page.locator('input[type=number]');", "await expect(input).toBeVisible();", "await input.fill('42');", "await expect(input).toHaveValue('42');"],
    "/horizontal_slider": ["const slider = page.locator('input[type=range]');", "await expect(slider).toBeVisible();", "await slider.focus();", "await page.keyboard.press('ArrowRight');", "await expect(page.locator('#range')).not.toHaveText('0');"],
    "/context_menu": ["const box = page.locator('#hot-spot');", "await expect(box).toBeVisible();", "page.once('dialog', async dialog => { expect(dialog.type()).toBe('alert'); await dialog.accept(); });", "await box.click({ button: 'right' });"],
    "/challenging_dom": [_h("Challenging DOM"), "await expect(page.locator('table')).toContainText('Lorem');", "await expect(page.locator('canvas')).toBeVisible();"],
    "/exit_intent": [_h("Exit Intent"), "await page.mouse.move(100, 100);", "await page.mouse.move(100, 0);", "await expect(page.locator('.modal')).toBeVisible();", "await page.getByText('Close').click();", "await expect(page.locator('.modal')).toBeHidden();"],
    "/jqueryui/menu": [_h("JQueryUI"), MENU_VISIBLE_STEP, "await expect(page.getByRole('link', { name: /Enabled/i })).toBeVisible();"],
    "/javascript_error": ["const errors: string[] = [];", "page.on('pageerror', e => errors.push(e.message));", "await page.reload({ waitUntil: 'domcontentloaded' });", "expect(errors.length).toBeGreaterThan(0);"],
    "/large": [_h("Large & Deep DOM"), "await expect(page.locator('#large-table')).toBeVisible();"],
    "/infinite_scroll": [_h("Infinite Scroll"), "const before = await page.locator('.jscroll-added').count();", "await page.mouse.wheel(0, 3000);", "await expect.poll(async () => page.locator('.jscroll-added').count()).toBeGreaterThanOrEqual(before);"],
    "/download": [_h("File Downloader"), "await expect(page.locator('a').first()).toBeVisible();"],
    "/forgot_password": [_h("Forgot Password"), "await expect(page.locator('#email')).toBeVisible();", "await expect(page.locator('#form_submit')).toBeVisible();"],
    "/geolocation": ["await context.grantPermissions(['geolocation']);", "await context.setGeolocation({ latitude: 17.3850, longitude: 78.4867 });", _h("Geolocation"), "await page.getByRole('button', { name: /Where am I/i }).click();", "await expect(page.locator('#lat-value')).toBeVisible();", "await expect(page.locator('#long-value')).toBeVisible();"],
    "/floating_menu": [_h("Floating Menu"), MENU_VISIBLE_STEP, "await page.mouse.wheel(0, 1500);", MENU_VISIBLE_STEP],
    "/shadowdom": [_h("Simple template"), "await expect(page.locator('my-paragraph')).toHaveCount(2);", "await expect(page.locator('body')).toContainText(/My default text|different text/i);"],
    "/frames": [_h("Frames"), _link("Nested Frames"), _link("iFrame")],
    "/windows": [_h("Opening a new window"), "const popupPromise = page.waitForEvent('popup');", "await page.getByRole('link', { name: /Click Here/i }).click();", "const popup = await popupPromise;", "await expect(popup.locator('body')).toContainText('New Window');"],
    "/shifting_content": [_h("Shifting Content"), _link("Example 1"), _link("Example 2"), _link("Example 3")],
}


def _safe_test_name(req: Dict[str, str]) -> str:
    return (f"{req.get('id', 'REQ')} {req.get('feature', 'requirement')}".replace("'", "").replace("\n", " "))[:150]


def _full_text(req: Dict[str, str]) -> str:
    return " ".join(req.get(k, "") for k in ("feature", "scenario", "expected")).lower()


def _generic_steps(req: Dict[str, str]) -> List[str]:
    heading = re.sub(r"\s*\([^)]*\)", "", req.get("feature", "")).split("–")[0].strip()
    return [BODY_VISIBLE_STEP, f"{BODY}.toContainText(/{re.escape(heading[:45])}/i);"] if heading and len(heading) < 80 else [BODY_VISIBLE_STEP, BODY_NOT_EMPTY_STEP]


def _login_steps(full: str) -> List[str]:
    if "successful" in full or "valid credentials" in full or "secure area" in full:
        return ["await page.locator('#username').fill('tomsmith');", "await page.locator('#password').fill('SuperSecretPassword!');", "await page.getByRole('button', { name: /login/i }).click();", "await expect(page).toHaveURL(/secure/);", "await expect(page.locator('#flash')).toContainText(/logged into a secure area/i);"]
    if any(k in full for k in ("invalid", "wrong", "error")):
        return ["await page.locator('#username').fill('invalid-user');", "await page.locator('#password').fill('invalid-password');", "await page.getByRole('button', { name: /login/i }).click();", "await expect(page.locator('#flash')).toContainText(/invalid/i);", "await expect(page).not.toHaveURL(/secure/);"]
    return ["await expect(page.getByRole('button', { name: /login/i })).toBeVisible();"]


def _alert_steps(full: str) -> List[str]:
    steps: List[str] = []
    if "alert" in full and "render" not in full:
        steps += ["page.once('dialog', async dialog => { expect(dialog.type()).toBe('alert'); await dialog.accept(); });", "await page.getByRole('button', { name: 'Click for JS Alert' }).click();", "await expect(page.locator('#result')).toContainText(/successfully/i);"]
    if "confirm" in full or "prompt" in full:
        steps += ["page.once('dialog', async dialog => { expect(dialog.type()).toBe('confirm'); await dialog.accept(); });", "await page.getByRole('button', { name: 'Click for JS Confirm' }).click();", "await expect(page.locator('#result')).toContainText(/Ok/i);", "page.once('dialog', async dialog => { expect(dialog.type()).toBe('prompt'); await dialog.accept('hello'); });", "await page.getByRole('button', { name: 'Click for JS Prompt' }).click();", "await expect(page.locator('#result')).toContainText('hello');"]
    return steps


def _conditional_steps(path: str, full: str) -> List[str]:
    cases = {
        CHECKBOXES_PATH: ["const first = boxes.first();", "const before = await first.isChecked();", "await first.click();", "expect(await first.isChecked()).toBe(!before);"] if "toggle" in full else [],
        LOGIN_PATH: _login_steps(full),
        DROPDOWN_PATH: ["await dropdown.selectOption({ label: 'Option 1' });", "await expect(dropdown).toHaveValue('1');"] if "selection" in full or "select" in full else [],
        UPLOAD_PATH: ["await page.locator('input[type=file]').setInputFiles({ name: 'sample.txt', mimeType: 'text/plain', buffer: Buffer.from('capstone upload') });", "await page.locator('#file-submit').click();", "await expect(page.getByRole('heading', { name: /File Uploaded/i })).toBeVisible();", "await expect(page.locator('#uploaded-files')).toContainText('sample.txt');"] if "upload" in full and "action" in full else [],
        JS_ALERTS_PATH: _alert_steps(full),
    }
    return cases.get(path, [])


def _is_nfr(req: Dict[str, str]) -> bool:
    return str(req.get("id", "")).upper().startswith("NFR") or str(req.get("type", "")).lower().startswith("non")


def _start_path(req: Dict[str, str], full: str) -> str:
    path = req.get("endpoint") or ROOT_PATH
    return LOGIN_PATH if path == SECURE_PATH and any(k in full for k in ["login", "credential", "tomsmith", "secure area"]) else path


def _coverage_steps(full: str) -> List[str]:
    return ["await expect(page.locator('body')).toContainText('Powered by Elemental Selenium');"] if FOOTER_TEXT in full else []


def generate_playwright_script(requirement: Dict[str, str], _feedback: str = "") -> str:
    req = requirement if isinstance(requirement, dict) else {"feature": str(requirement), "endpoint": ROOT_PATH}
    full = _full_text(req)
    path = _start_path(req, full)
    base_steps = [BODY_VISIBLE_STEP, BODY_NOT_EMPTY_STEP] if _is_nfr(req) else BASE_CASES.get(path, _generic_steps(req))
    steps = base_steps if _is_nfr(req) else base_steps + _conditional_steps(path, full) + _coverage_steps(full)
    body = "\n".join(f"  {step}" for step in steps)
    return f"{HEADER}test('{_safe_test_name(req)}', async ({{ page, context }}) => {{\n  await page.goto('{path}', {{ waitUntil: 'domcontentloaded' }});\n{body}\n}});\n"
