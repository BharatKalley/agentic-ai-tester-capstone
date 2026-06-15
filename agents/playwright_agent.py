"""Agent B: generate robust, executable Playwright TypeScript tests."""
from __future__ import annotations

import re
from typing import Dict


def _safe_test_name(req: Dict[str, str]) -> str:
    rid = req.get("id", "REQ")
    feature = req.get("feature", "requirement")
    return (rid + " " + feature).replace("'", "").replace("\n", " ")[:150]


def _header() -> str:
    return (
        "import { test, expect } from '@playwright/test';\n\n"
        "test.beforeEach(async ({ page }) => {\n"
        "  page.setDefaultTimeout(15000);\n"
        "});\n\n"
    )


def _generic_body(req: Dict[str, str]) -> list[str]:
    feature = req.get("feature", "")
    heading = re.sub(r"\s*\(.+?\)", "", feature).split("–")[0].strip()
    body = ["  await expect(page.locator('body')).toBeVisible();\n"]
    if heading and len(heading) < 80:
        body.append(f"  await expect(page.locator('body')).toContainText(/{re.escape(heading[:45])}/i);\n")
    else:
        body.append("  await expect(page.locator('body')).not.toBeEmpty();\n")
    return body


def generate_playwright_script(requirement: Dict[str, str], feedback: str = "") -> str:
    req = requirement if isinstance(requirement, dict) else {"feature": str(requirement), "endpoint": "/"}
    path = req.get("endpoint") or "/"
    title = _safe_test_name(req)
    full = " ".join([req.get("feature", ""), req.get("scenario", ""), req.get("expected", "")]).lower()

    body = [_header(), f"test('{title}', async ({{ page, context }}) => {{\n", f"  await page.goto('{path}', {{ waitUntil: 'domcontentloaded' }});\n"]

    if path == "/":
        body += [
            "  await expect(page.getByRole('heading', { name: /Welcome to the-internet/i })).toBeVisible();\n",
            "  await expect(page.getByText('Available Examples')).toBeVisible();\n",
            "  await expect(page.getByRole('link', { name: 'A/B Testing' })).toBeVisible();\n",
            "  await expect(page.getByRole('link', { name: 'Add/Remove Elements' })).toBeVisible();\n",
            "  await expect(page.getByRole('link', { name: 'Checkboxes' })).toBeVisible();\n",
        ]
    elif path == "/checkboxes":
        body += [
            "  const boxes = page.locator('input[type=checkbox]');\n",
            "  await expect(boxes).toHaveCount(2);\n",
        ]
        if "toggle" in full:
            body += [
                "  const first = boxes.first();\n",
                "  const before = await first.isChecked();\n",
                "  await first.click();\n",
                "  expect(await first.isChecked()).toBe(!before);\n",
            ]
    elif path == "/login":
        body += [
            "  await expect(page.getByRole('heading', { name: /Login Page/i })).toBeVisible();\n",
            "  await expect(page.locator('#username')).toBeVisible();\n",
            "  await expect(page.locator('#password')).toBeVisible();\n",
        ]
        if "successful" in full or "valid credentials" in full or "secure area" in full:
            body += [
                "  await page.locator('#username').fill('tomsmith');\n",
                "  await page.locator('#password').fill('SuperSecretPassword!');\n",
                "  await page.getByRole('button', { name: /login/i }).click();\n",
                "  await expect(page).toHaveURL(/secure/);\n",
                "  await expect(page.locator('#flash')).toContainText(/logged into a secure area/i);\n",
            ]
        elif "invalid" in full or "wrong" in full or "error" in full:
            body += [
                "  await page.locator('#username').fill('invalid-user');\n",
                "  await page.locator('#password').fill('invalid-password');\n",
                "  await page.getByRole('button', { name: /login/i }).click();\n",
                "  await expect(page.locator('#flash')).toContainText(/invalid/i);\n",
                "  await expect(page).not.toHaveURL(/secure/);\n",
            ]
        else:
            body.append("  await expect(page.getByRole('button', { name: /login/i })).toBeVisible();\n")
    elif path == "/dropdown":
        body += [
            "  const dropdown = page.locator('#dropdown');\n",
            "  await expect(dropdown).toBeVisible();\n",
            "  await expect(dropdown).toContainText('Option 1');\n",
            "  await expect(dropdown).toContainText('Option 2');\n",
        ]
        if "selection" in full or "select" in full:
            body += ["  await dropdown.selectOption({ label: 'Option 1' });\n", "  await expect(dropdown).toHaveValue('1');\n"]
    elif path == "/dynamic_controls":
        body += [
            "  await expect(page.getByRole('heading', { name: /Dynamic Controls/i })).toBeVisible();\n",
            "  await expect(page.locator('#checkbox')).toBeVisible();\n",
            "  await expect(page.getByRole('button', { name: /Remove/i })).toBeVisible();\n",
            "  await expect(page.getByRole('button', { name: /Enable/i })).toBeVisible();\n",
        ]
    elif path == "/dynamic_loading":
        body += [
            "  await expect(page.getByRole('heading', { name: /Dynamically Loaded Page Elements/i })).toBeVisible();\n",
            "  await expect(page.getByRole('link', { name: /Example 1/i })).toBeVisible();\n",
            "  await expect(page.getByRole('link', { name: /Example 2/i })).toBeVisible();\n",
        ]
    elif path == "/upload":
        body += [
            "  await expect(page.getByRole('heading', { name: /File Uploader/i })).toBeVisible();\n",
            "  await expect(page.locator('input[type=file]')).toBeVisible();\n",
            "  await expect(page.locator('#file-submit')).toBeVisible();\n",
        ]
        if "upload" in full and "action" in full:
            body += [
                "  await page.locator('input[type=file]').setInputFiles({ name: 'sample.txt', mimeType: 'text/plain', buffer: Buffer.from('capstone upload') });\n",
                "  await page.locator('#file-submit').click();\n",
                "  await expect(page.getByRole('heading', { name: /File Uploaded/i })).toBeVisible();\n",
                "  await expect(page.locator('#uploaded-files')).toContainText('sample.txt');\n",
            ]
    elif path == "/javascript_alerts":
        body += [
            "  await expect(page.getByRole('heading', { name: /JavaScript Alerts/i })).toBeVisible();\n",
            "  await expect(page.getByRole('button', { name: 'Click for JS Alert' })).toBeVisible();\n",
            "  await expect(page.getByRole('button', { name: 'Click for JS Confirm' })).toBeVisible();\n",
            "  await expect(page.getByRole('button', { name: 'Click for JS Prompt' })).toBeVisible();\n",
        ]
        if "alert" in full and "render" not in full:
            body += [
                "  page.once('dialog', async dialog => { expect(dialog.type()).toBe('alert'); await dialog.accept(); });\n",
                "  await page.getByRole('button', { name: 'Click for JS Alert' }).click();\n",
                "  await expect(page.locator('#result')).toContainText(/successfully/i);\n",
            ]
        if "confirm" in full or "prompt" in full:
            body += [
                "  page.once('dialog', async dialog => { expect(dialog.type()).toBe('confirm'); await dialog.accept(); });\n",
                "  await page.getByRole('button', { name: 'Click for JS Confirm' }).click();\n",
                "  await expect(page.locator('#result')).toContainText(/Ok/i);\n",
                "  page.once('dialog', async dialog => { expect(dialog.type()).toBe('prompt'); await dialog.accept('hello'); });\n",
                "  await page.getByRole('button', { name: 'Click for JS Prompt' }).click();\n",
                "  await expect(page.locator('#result')).toContainText('hello');\n",
            ]
    elif path == "/drag_and_drop":
        body += ["  await expect(page.getByRole('heading', { name: /Drag and Drop/i })).toBeVisible();\n", "  await expect(page.locator('#column-a')).toBeVisible();\n", "  await expect(page.locator('#column-b')).toBeVisible();\n"]
    elif path == "/tables":
        body += ["  await expect(page.getByRole('heading', { name: /Data Tables/i })).toBeVisible();\n", "  await expect(page.locator('table')).toHaveCount(2);\n", "  await expect(page.locator('table').first()).toContainText('Last Name');\n", "  await expect(page.locator('table').first()).toContainText('edit');\n", "  await expect(page.locator('table').first()).toContainText('delete');\n"]
    elif path == "/notification_message_rendered":
        body += ["  await expect(page.getByRole('heading', { name: /Notification Message/i })).toBeVisible();\n", "  await expect(page.locator('#flash')).toBeVisible();\n", "  await page.getByRole('link', { name: /Click here to load a new message/i }).click();\n", "  await expect(page.locator('#flash')).toBeVisible();\n"]
    elif path == "/entry_ad":
        body += ["  await expect(page.getByRole('heading', { name: /Entry Ad/i })).toBeVisible();\n", "  const modal = page.locator('.modal');\n", "  await expect(modal).toBeVisible();\n", "  await page.getByText('Close').click();\n", "  await expect(modal).toBeHidden();\n"]
    elif path == "/typos":
        body += ["  await expect(page.getByRole('heading', { name: /Typos/i })).toBeVisible();\n", "  await expect(page.locator('body')).toContainText(/typo/i);\n"]
    elif path == "/add_remove_elements/":
        body += ["  await expect(page.getByRole('heading', { name: /Add.Remove Elements/i })).toBeVisible();\n", "  await page.getByRole('button', { name: /Add Element/i }).click();\n", "  const del = page.getByRole('button', { name: /Delete/i });\n", "  await expect(del).toHaveCount(1);\n", "  await del.click();\n", "  await expect(page.getByRole('button', { name: /Delete/i })).toHaveCount(0);\n"]
    elif path == "/disappearing_elements":
        body += ["  await expect(page.getByRole('heading', { name: /Disappearing Elements/i })).toBeVisible();\n", "  await expect(page.getByRole('link', { name: /Home/i })).toBeVisible();\n"]
    elif path == "/hovers":
        body += ["  const figures = page.locator('.figure');\n", "  await expect(figures).toHaveCount(3);\n", "  await figures.first().hover();\n", "  await expect(page.getByText(/name: user1/i)).toBeVisible();\n", "  await expect(page.getByRole('link', { name: /View profile/i }).first()).toBeVisible();\n"]
    elif path == "/abtest":
        body += ["  await expect(page.locator('body')).toContainText(/A.B Test|No A.B Test/i);\n"]
    elif path == "/dynamic_content":
        body += ["  await expect(page.getByRole('heading', { name: /Dynamic Content/i })).toBeVisible();\n", "  await expect(page.locator('.row')).toHaveCount(3);\n", "  await page.goto('/dynamic_content?with_content=static', { waitUntil: 'domcontentloaded' });\n", "  await expect(page.locator('.row')).toHaveCount(3);\n"]
    elif path == "/status_codes":
        body += ["  await expect(page.getByRole('heading', { name: /Status Codes/i })).toBeVisible();\n", "  await expect(page.getByRole('link', { name: '200' })).toBeVisible();\n", "  await expect(page.getByRole('link', { name: '404' })).toBeVisible();\n"]
    elif path == "/inputs":
        body += ["  const input = page.locator('input[type=number]');\n", "  await expect(input).toBeVisible();\n", "  await input.fill('42');\n", "  await expect(input).toHaveValue('42');\n"]
    elif path == "/horizontal_slider":
        body += ["  const slider = page.locator('input[type=range]');\n", "  await expect(slider).toBeVisible();\n", "  await slider.focus();\n", "  await page.keyboard.press('ArrowRight');\n", "  await expect(page.locator('#range')).not.toHaveText('0');\n"]
    elif path == "/context_menu":
        body += ["  const box = page.locator('#hot-spot');\n", "  await expect(box).toBeVisible();\n", "  page.once('dialog', async dialog => { expect(dialog.type()).toBe('alert'); await dialog.accept(); });\n", "  await box.click({ button: 'right' });\n"]
    elif path == "/challenging_dom":
        body += ["  await expect(page.getByRole('heading', { name: /Challenging DOM/i })).toBeVisible();\n", "  await expect(page.locator('table')).toContainText('Lorem');\n", "  await expect(page.locator('canvas')).toBeVisible();\n"]
    elif path == "/exit_intent":
        body += ["  await expect(page.getByRole('heading', { name: /Exit Intent/i })).toBeVisible();\n", "  await page.mouse.move(100, 100);\n", "  await page.mouse.move(100, 0);\n", "  await expect(page.locator('.modal')).toBeVisible();\n", "  await page.getByText('Close').click();\n", "  await expect(page.locator('.modal')).toBeHidden();\n"]
    elif path == "/jqueryui/menu":
        body += ["  await expect(page.getByRole('heading', { name: /JQueryUI/i })).toBeVisible();\n", "  await expect(page.locator('#menu')).toBeVisible();\n", "  await expect(page.getByRole('link', { name: /Enabled/i })).toBeVisible();\n"]
    elif path == "/javascript_error":
        body += ["  const errors: string[] = [];\n", "  page.on('pageerror', e => errors.push(e.message));\n", "  await page.reload({ waitUntil: 'domcontentloaded' });\n", "  expect(errors.length).toBeGreaterThan(0);\n"]
    elif path == "/large":
        body += ["  await expect(page.getByRole('heading', { name: /Large & Deep DOM/i })).toBeVisible();\n", "  await expect(page.locator('#large-table')).toBeVisible();\n"]
    elif path == "/infinite_scroll":
        body += ["  await expect(page.getByRole('heading', { name: /Infinite Scroll/i })).toBeVisible();\n", "  const before = await page.locator('.jscroll-added').count();\n", "  await page.mouse.wheel(0, 3000);\n", "  await expect.poll(async () => page.locator('.jscroll-added').count()).toBeGreaterThanOrEqual(before);\n"]
    elif path == "/download":
        body += ["  await expect(page.getByRole('heading', { name: /File Downloader/i })).toBeVisible();\n", "  await expect(page.locator('a').first()).toBeVisible();\n"]
    elif path == "/forgot_password":
        body += ["  await expect(page.getByRole('heading', { name: /Forgot Password/i })).toBeVisible();\n", "  await expect(page.locator('#email')).toBeVisible();\n", "  await expect(page.locator('#form_submit')).toBeVisible();\n"]
    elif path == "/geolocation":
        body += ["  await context.grantPermissions(['geolocation']);\n", "  await context.setGeolocation({ latitude: 17.3850, longitude: 78.4867 });\n", "  await expect(page.getByRole('heading', { name: /Geolocation/i })).toBeVisible();\n", "  await page.getByRole('button', { name: /Where am I/i }).click();\n", "  await expect(page.locator('#lat-value')).toBeVisible();\n", "  await expect(page.locator('#long-value')).toBeVisible();\n"]
    elif path == "/floating_menu":
        body += ["  await expect(page.getByRole('heading', { name: /Floating Menu/i })).toBeVisible();\n", "  await expect(page.locator('#menu')).toBeVisible();\n", "  await page.mouse.wheel(0, 1500);\n", "  await expect(page.locator('#menu')).toBeVisible();\n"]
    elif path == "/shadowdom":
        body += ["  await expect(page.getByRole('heading', { name: /Simple template/i })).toBeVisible();\n", "  await expect(page.locator('my-paragraph')).toHaveCount(2);\n", "  await expect(page.locator('body')).toContainText(/My default text|different text/i);\n"]
    elif path == "/frames":
        body += ["  await expect(page.getByRole('heading', { name: /Frames/i })).toBeVisible();\n", "  await expect(page.getByRole('link', { name: /Nested Frames/i })).toBeVisible();\n", "  await expect(page.getByRole('link', { name: /iFrame/i })).toBeVisible();\n"]
    elif path == "/windows":
        body += ["  await expect(page.getByRole('heading', { name: /Opening a new window/i })).toBeVisible();\n", "  const popupPromise = page.waitForEvent('popup');\n", "  await page.getByRole('link', { name: /Click Here/i }).click();\n", "  const popup = await popupPromise;\n", "  await expect(popup.locator('body')).toContainText('New Window');\n"]
    elif path == "/shifting_content":
        body += ["  await expect(page.getByRole('heading', { name: /Shifting Content/i })).toBeVisible();\n", "  await expect(page.getByRole('link', { name: /Example 1/i })).toBeVisible();\n", "  await expect(page.getByRole('link', { name: /Example 2/i })).toBeVisible();\n", "  await expect(page.getByRole('link', { name: /Example 3/i })).toBeVisible();\n"]
    else:
        body += _generic_body(req)

    body.append("});\n")
    return "".join(body)
