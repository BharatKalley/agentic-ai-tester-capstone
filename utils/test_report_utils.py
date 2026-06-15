"""
Utilities for managing and reporting test execution results.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class ReportManager:
    """Manage test execution reports and storage."""
    __test__ = False
    
    def __init__(self, report_dir: str = "reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
    
    def save_report(self, results: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Save test results to a JSON report file.
        
        Args:
            results: Dictionary containing test results
            filename: Optional custom filename (without extension)
        
        Returns:
            Path to saved report file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
        elif not filename.endswith(".json"):
            filename = f"{filename}.json"
        
        filepath = self.report_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)
        
        return str(filepath)
    
    def load_report(self, filename: str) -> Dict[str, Any]:
        """
        Load a saved test report.
        
        Args:
            filename: Report filename
        
        Returns:
            Report data as dictionary
        """
        filepath = self.report_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Report not found: {filepath}")
        
        with open(filepath, "r") as f:
            return json.load(f)
    
    def list_reports(self) -> List[str]:
        """List all available test reports."""
        return [f.name for f in self.report_dir.glob("*.json")]
    
    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """Get the most recent test report."""
        reports = sorted(self.report_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
        
        if not reports:
            return None
        
        with open(reports[0], "r") as f:
            return json.load(f)
    
    def generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate a text summary of test results."""
        summary = []
        summary.append("=" * 60)
        summary.append("TEST EXECUTION SUMMARY")
        summary.append("=" * 60)
        
        if isinstance(results, list):
            total = len(results)
            passed = sum(1 for r in results if r.get("execution", {}).get("status") == "PASSED")
            failed = total - passed
            validation_passed = sum(1 for r in results if "PASS" in r.get("validation", "").upper())
            
            summary.append(f"\nTotal Requirements: {total}")
            summary.append(f"Validation Passed: {validation_passed}")
            summary.append(f"Tests Passed: {passed}")
            summary.append(f"Tests Failed: {failed}")
            summary.append(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
            
            summary.append("\n" + "-" * 60)
            summary.append("DETAILED RESULTS")
            summary.append("-" * 60)
            
            for idx, res in enumerate(results, 1):
                feature = res['requirement'].get('feature', 'Unknown')
                validation = "✅ PASS" if "PASS" in res.get('validation', '').upper() else "❌ FAIL"
                execution = res.get("execution", {})
                exec_status = f"✅ {execution.get('status')}" if execution.get("status") == "PASSED" else f"❌ {execution.get('status')}"
                
                summary.append(f"\n{idx}. {feature}")
                summary.append(f"   Validation: {validation}")
                summary.append(f"   Execution: {exec_status}")
                
                if execution.get("error"):
                    summary.append(f"   Error: {execution['error']}")
        
        else:
            # Handle single execution result
            if results.get("total_tests"):
                summary.append(f"\nTotal Tests: {results['total_tests']}")
                summary.append(f"Passed: {results.get('passed', 0)}")
                summary.append(f"Failed: {results.get('failed', 0)}")
                summary.append(f"Status: {results.get('status', 'UNKNOWN')}")
        
        summary.append("\n" + "=" * 60)
        return "\n".join(summary)


class ResultComparator:
    """Compare test results from different runs."""
    __test__ = False
    
    @staticmethod
    def compare_results(previous: List[Dict], current: List[Dict]) -> Dict[str, Any]:
        """
        Compare two sets of test results.
        
        Args:
            previous: Previous test results
            current: Current test results
        
        Returns:
            Dictionary with comparison analysis
        """
        comparison = {
            "total_previous": len(previous),
            "total_current": len(current),
            "improved": [],
            "regressed": [],
            "unchanged": []
        }
        
        for curr_res in current:
            curr_feature = curr_res['requirement'].get('feature')
            prev_res = next(
                (r for r in previous if r['requirement'].get('feature') == curr_feature),
                None
            )
            
            if not prev_res:
                continue
            
            prev_status = prev_res.get("execution", {}).get("status")
            curr_status = curr_res.get("execution", {}).get("status")
            
            result_item = {
                "feature": curr_feature,
                "previous": prev_status,
                "current": curr_status
            }
            
            if prev_status == "FAILED" and curr_status == "PASSED":
                comparison["improved"].append(result_item)
            elif prev_status == "PASSED" and curr_status == "FAILED":
                comparison["regressed"].append(result_item)
            else:
                comparison["unchanged"].append(result_item)
        
        return comparison
    
    @staticmethod
    def identify_flaky_tests(historical_results: List[Dict]) -> List[Dict[str, Any]]:
        """
        Identify potentially flaky tests (inconsistent results).
        
        Args:
            historical_results: List of multiple test run results
        
        Returns:
            List of flaky tests with their inconsistency pattern
        """
        test_statuses = {}
        
        for run_results in historical_results:
            for result in run_results if isinstance(run_results, list) else [run_results]:
                feature = result['requirement'].get('feature')
                status = result.get("execution", {}).get("status")
                
                if feature not in test_statuses:
                    test_statuses[feature] = []
                test_statuses[feature].append(status)
        
        flaky_tests = []
        for feature, statuses in test_statuses.items():
            # A test is flaky if it has mixed results
            if len(set(statuses)) > 1:
                flaky_tests.append({
                    "feature": feature,
                    "inconsistent_statuses": list(set(statuses)),
                    "pass_rate": sum(1 for s in statuses if s == "PASSED") / len(statuses),
                    "runs": len(statuses)
                })
        
        return flaky_tests


TestReportManager = ReportManager
TestComparator = ResultComparator


def format_test_results_table(results: List[Dict[str, Any]]) -> str:
    """Generate a formatted table of test results."""
    table = []
    table.append("┌─────┬──────────────────┬────────────┬──────────────┐")
    table.append("│ No. │ Feature          │ Validation │ Execution    │")
    table.append("├─────┼──────────────────┼────────────┼──────────────┤")
    
    for idx, res in enumerate(results, 1):
        feature = res['requirement'].get('feature', 'Unknown')[:16]
        validation = "✅ PASS" if "PASS" in res.get('validation', '').upper() else "❌ FAIL"
        execution = "✅ PASS" if res.get("execution", {}).get("status") == "PASSED" else "❌ FAIL"
        
        table.append(f"│ {idx:3} │ {feature:<16} │ {validation:<10} │ {execution:<12} │")
    
    table.append("└─────┴──────────────────┴────────────┴──────────────┘")
    return "\n".join(table)


def export_results_csv(results: List[Dict[str, Any]], filepath: str) -> None:
    """Export test results to CSV format."""
    import csv
    
    with open(filepath, "w", newline="") as csvfile:
        fieldnames = ["Feature", "Scenario", "Validation", "Execution Status", "Error"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for res in results:
            writer.writerow({
                "Feature": res['requirement'].get('feature', 'Unknown'),
                "Scenario": res['requirement'].get('scenario', 'Unknown'),
                "Validation": "PASS" if "PASS" in res.get('validation', '').upper() else "FAIL",
                "Execution Status": res.get("execution", {}).get("status", "UNKNOWN"),
                "Error": res.get("execution", {}).get("error", "")
            })


def export_results_html(results: List[Dict[str, Any]], filepath: str) -> None:
    """Export test results to HTML format."""
    passed = sum(1 for r in results if r.get("execution", {}).get("status") == "PASSED")
    failed = len(results) - passed
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Execution Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .pass {{ background-color: #d4edda; }}
        .fail {{ background-color: #f8d7da; }}
    </style>
</head>
<body>
    <h1>Test Execution Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {len(results)}</p>
        <p class="passed">✅ Passed: {passed}</p>
        <p class="failed">❌ Failed: {failed}</p>
        <p>Success Rate: {(passed/len(results)*100):.1f}%</p>
    </div>
    
    <h2>Detailed Results</h2>
    <table>
        <tr>
            <th>Feature</th>
            <th>Scenario</th>
            <th>Validation</th>
            <th>Execution</th>
            <th>Error</th>
        </tr>
"""
    
    for res in results:
        exec_status = res.get("execution", {}).get("status", "UNKNOWN")
        row_class = "pass" if exec_status == "PASSED" else "fail"
        
        html += f"""
        <tr class="{row_class}">
            <td>{res['requirement'].get('feature', 'Unknown')}</td>
            <td>{res['requirement'].get('scenario', 'Unknown')}</td>
            <td>{"✅ PASS" if "PASS" in res.get('validation', '').upper() else "❌ FAIL"}</td>
            <td>{exec_status}</td>
            <td>{res.get("execution", {}).get("error", "")}</td>
        </tr>
"""
    
    html += """
    </table>
</body>
</html>
"""
    
    with open(filepath, "w") as f:
        f.write(html)
