"""Verification report generation"""

import json
from datetime import datetime
from pathlib import Path
from .models import VerificationResult


class ReportGenerator:
    """Generate verification reports in multiple formats"""
    
    def save_report(self, result: VerificationResult, output_path: Path):
        """Save verification report as JSON"""
        report = self._build_report(result)
        
        # Save JSON
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Also save human-readable summary
        summary_path = output_path.with_suffix('.txt')
        with open(summary_path, 'w') as f:
            f.write(self._build_text_report(result))
    
    def _build_report(self, result: VerificationResult) -> dict:
        """Build report dictionary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "generator": result.generator_path,
            "domain": result.domain,
            "status": "PASS" if result.passed else "FAIL",
            "summary": {
                "total_issues": result.total_issues,
                "critical_issues": result.critical_issues,
                "warning_issues": result.warning_issues
            },
            "steps": [
                {
                    "name": step.step_name,
                    "passed": step.passed,
                    "issues": [
                        {
                            "severity": issue.severity.value,
                            "message": issue.message,
                            "details": issue.details,
                            "file": issue.file_path
                        }
                        for issue in step.issues
                    ],
                    "details": step.details
                }
                for step in result.steps
            ]
        }
    
    def _build_text_report(self, result: VerificationResult) -> str:
        """Build human-readable text report"""
        lines = []
        lines.append("=" * 60)
        lines.append("VERIFICATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Generator: {result.generator_path}")
        lines.append(f"Domain: {result.domain or 'N/A'}")
        lines.append(f"Status: {'✅ PASS' if result.passed else '❌ FAIL'}")
        lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        lines.append("SUMMARY")
        lines.append("-" * 60)
        lines.append(f"Total Issues: {result.total_issues}")
        lines.append(f"  - Critical: {result.critical_issues}")
        lines.append(f"  - Warnings: {result.warning_issues}")
        lines.append("")
        
        for step in result.steps:
            lines.append(f"\n{step.step_name}")
            lines.append("-" * 60)
            lines.append(f"Status: {'✅ PASS' if step.passed else '❌ FAIL'}")
            
            if step.issues:
                lines.append(f"\nIssues ({len(step.issues)}):")
                for issue in step.issues:
                    icon = "🔴" if issue.severity.value == "critical" else "⚠️" if issue.severity.value == "warning" else "ℹ️"
                    lines.append(f"  {icon} [{issue.severity.value.upper()}] {issue.message}")
                    if issue.details:
                        lines.append(f"     Details: {issue.details}")
                    if issue.file_path:
                        lines.append(f"     File: {issue.file_path}")
            else:
                lines.append("  No issues found")
            
            if step.details:
                lines.append(f"\nDetails: {step.details}")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
