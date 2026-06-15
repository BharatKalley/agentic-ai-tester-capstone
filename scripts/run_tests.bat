@echo off
call venv\Scripts\activate
npx playwright test
npx playwright show-report
