from __future__ import annotations

import argparse
import json
from agents.orchestrator import run_workflow, run_execution_only


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic AI Tester CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Extract SRS requirements, generate Playwright tests, and let Agent C validate/execute/fix them")
    gen.add_argument("pdf", help="Path to SRS PDF, for example data/uploaded_srs.pdf")
    gen.add_argument("--no-execute", action="store_true", help="Only statically validate. Not recommended for capstone demo.")
    gen.add_argument("--max-requirements", type=int, default=None, help="Limit requirements for quick demo")
    gen.add_argument("--no-clean", action="store_true", help="Do not delete old generated .spec.ts files first")

    run = sub.add_parser("test", help="Run generated Playwright tests")
    run.add_argument("test_dir", nargs="?", default="generated_tests")

    args = parser.parse_args()
    if args.command == "generate":
        result = run_workflow(args.pdf, execute_tests=not args.no_execute, max_requirements=args.max_requirements, clean=not args.no_clean)
    else:
        result = run_execution_only(args.test_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
