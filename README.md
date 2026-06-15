# Agentic AI Tester

This project implements the full capstone workflow:

- **Agent A** extracts atomic, testable requirements from an SRS PDF.
- **Agent B** generates executable Playwright TypeScript scripts.
- **Agent C** validates scripts for hallucinations, missing coverage, edge-case gaps, and Playwright execution failures.
- Agent C sends targeted feedback back to Agent B and selectively regenerates only failed/missing scripts.
- The repair loop stops after **maximum 5 attempts** and writes the final outcome.

## Folder Structure

```text
agentic-ai-tester
├── agents/
│   ├── extractor_agent.py       # Agent A
│   ├── playwright_agent.py      # Agent B
│   ├── validator_agent.py       # Agent C static validation
│   ├── executor_agent.py        # Agent C Playwright execution
│   └── orchestrator.py          # Agent A -> B -> C loop
├── data/                        # Place SRS PDF here
├── generated_tests/             # Generated .spec.ts files
├── requirements/                # extracted_requirements.json
├── feedback/                    # Agent C feedback per failed attempt
├── coverage/                    # coverage_matrix.json
├── execution/                   # Playwright run results
├── reports/                     # iteration reports + final_report.json
├── cli.py
├── app.py
├── package.json
├── playwright.config.ts
└── requirements.txt
```

## Setup on Windows

```powershell
cd D:\agentic-ai-tester
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
npm install
npx playwright install
```

## Place Your SRS PDF

You can keep your original filename:

```text
data\Software Requirements Specification.pdf
```

## Generate, Validate, Execute, and Auto-Fix

```powershell
python cli.py generate "data\Software Requirements Specification.pdf"
```

This command runs the full capstone loop:

1. Agent A extracts requirements.
2. Agent B generates Playwright tests.
3. Agent C validates and executes each test.
4. Agent C sends feedback and Agent B regenerates failed scripts only.
5. Loop stops after 5 attempts.

## Run Only the Generated Tests

```powershell
npx playwright test generated_tests
```

Open the report:

```powershell
npx playwright show-report
```

## Important Output Files for Submission

```text
requirements/extracted_requirements.json
coverage/coverage_matrix.json
feedback/*.json
execution/playwright_results.json
reports/iteration_*.json
reports/final_report.json
reports/latest_validation_report.json
```

These files prove that the multi-agent workflow, coverage validation, self-healing feedback loop, and max-5-attempt rule are implemented.

## Quick Demo Command

To demo only the first few requirements:

```powershell
python cli.py generate "data\Software Requirements Specification.pdf" --max-requirements 5
```

## Troubleshooting

If scripts fail because old generated files remain:

```powershell
del /Q generated_tests\*.spec.ts
python cli.py generate "data\Software Requirements Specification.pdf"
```

If Node or npm is blocked in PowerShell:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
