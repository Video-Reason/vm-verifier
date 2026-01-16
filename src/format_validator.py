"""Code format and naming validation"""

import ast
import re
from pathlib import Path
from typing import List, Optional
from .models import Issue, Severity, StepResult


class FormatValidator:
    """Validates code format, naming conventions, and compliance"""
    
    def validate(self, extracted_path: Path) -> StepResult:
        """Validate code format and naming"""
        issues: List[Issue] = []
        
        # Extract domain from config.py
        domain = self._extract_domain(extracted_path, issues)
        
        # Validate domain format
        if domain:
            self._validate_domain_format(domain, issues)
        
        # Check task_id format in base_generator.py
        self._check_task_id_format(extracted_path, issues)
        
        # Check output file naming
        self._check_output_naming(extracted_path, issues)
        
        # Check requirements.txt
        self._check_requirements(extracted_path, issues)
        
        return StepResult(
            step_name="Code Format Check",
            passed=len([i for i in issues if i.severity == Severity.CRITICAL]) == 0,
            issues=issues,
            details={"domain": domain}
        )
    
    def _extract_domain(self, extracted_path: Path, issues: List[Issue]) -> Optional[str]:
        """Extract domain from config.py"""
        config_path = extracted_path / "src/config.py"
        if not config_path.exists():
            return None
        
        content = config_path.read_text()
        
        # Try to parse with AST
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        if item.target.id == "domain":
                            # Handle direct assignment: domain: str = "value"
                            if isinstance(item.value, ast.Constant):
                                return item.value.value
                            # Handle Field assignment: domain: str = Field(default="value")
                            elif isinstance(item.value, ast.Call):
                                for keyword in item.value.keywords:
                                    if keyword.arg == "default" and isinstance(keyword.value, ast.Constant):
                                        return keyword.value.value
        
        # Fallback: regex search for common patterns
        patterns = [
            r'domain\s*[:=]\s*Field\s*\(\s*default\s*=\s*["\']([^"\']+)["\']',  # Field(default="x")
            r'domain\s*[:=]\s*["\']([^"\']+)["\']',  # Direct assignment
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        issues.append(Issue(
            step="format",
            severity=Severity.CRITICAL,
            message="Could not extract 'domain' from config.py",
            file_path="src/config.py"
        ))
        return None
    
    def _validate_domain_format(self, domain: str, issues: List[Issue]):
        """Validate domain naming convention"""
        if not re.match(r'^[a-z][a-z0-9_]*$', domain):
            issues.append(Issue(
                step="format",
                severity=Severity.CRITICAL,
                message=f"Invalid domain format: '{domain}'",
                details="Domain must be lowercase with underscores (e.g., 'my_task', not 'MyTask')",
                file_path="src/config.py"
            ))
        
        if domain.startswith("_") or domain.endswith("_"):
            issues.append(Issue(
                step="format",
                severity=Severity.WARNING,
                message=f"Domain should not start/end with underscore: '{domain}'",
                file_path="src/config.py"
            ))
    
    def _check_task_id_format(self, extracted_path: Path, issues: List[Issue]):
        """Check task_id generation format"""
        # Check in base_generator.py from core submodule
        base_gen_path = extracted_path / "core/base_generator.py"
        if not base_gen_path.exists():
            issues.append(Issue(
                step="format",
                severity=Severity.WARNING,
                message="Cannot verify task_id format - core/base_generator.py not found",
                details="Expected format: {domain}_{i:04d} starting from 0000"
            ))
            return
        
        content = base_gen_path.read_text()
        
        # Check for correct format: {domain}_{i:04d}
        if "{domain}_{i:04d}" not in content and '{self.config.domain}_{i:04d}' not in content:
            issues.append(Issue(
                step="format",
                severity=Severity.CRITICAL,
                message="Incorrect task_id format in base_generator.py",
                details="Should use format: {domain}_{i:04d} (e.g., maze_0000, maze_0001)",
                file_path="core/base_generator.py"
            ))
        
        # Check starting index
        if "range(num_samples)" in content or "range(1, num_samples" in content:
            issues.append(Issue(
                step="format",
                severity=Severity.CRITICAL,
                message="task_id should start from 0000, not 1",
                details="Use range(num_samples), not range(1, num_samples+1)",
                file_path="core/base_generator.py"
            ))
    
    def _check_output_naming(self, extracted_path: Path, issues: List[Issue]):
        """Check output file naming conventions"""
        output_writer_path = extracted_path / "core/output_writer.py"
        if not output_writer_path.exists():
            return
        
        content = output_writer_path.read_text()
        
        # Check video filename
        if "ground_truth.mp4" not in content:
            issues.append(Issue(
                step="format",
                severity=Severity.CRITICAL,
                message="Video file must be named 'ground_truth.mp4'",
                file_path="core/output_writer.py"
            ))
        
        # Check required output files
        required_outputs = ["first_frame.png", "final_frame.png", "prompt.txt"]
        for filename in required_outputs:
            if filename not in content:
                issues.append(Issue(
                    step="format",
                    severity=Severity.WARNING,
                    message=f"Expected output file '{filename}' not found in writer",
                    file_path="core/output_writer.py"
                ))
    
    def _check_requirements(self, extracted_path: Path, issues: List[Issue]):
        """Check requirements.txt for cleanliness"""
        req_path = extracted_path / "requirements.txt"
        if not req_path.exists():
            return
        
        content = req_path.read_text()
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        
        # Check for version pinning
        unpinned = [line for line in lines if '==' not in line and line]
        if unpinned:
            issues.append(Issue(
                step="format",
                severity=Severity.WARNING,
                message=f"Unpinned dependencies found: {', '.join(unpinned[:3])}",
                details="Consider pinning versions (e.g., package==1.2.3)",
                file_path="requirements.txt"
            ))
