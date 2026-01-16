"""File structure validation"""

from pathlib import Path
from typing import List, Set
from .models import Issue, Severity, StepResult


class StructureValidator:
    """Validates generator file structure and required files"""
    
    REQUIRED_FILES = {
        "src/generator.py",
        "src/config.py", 
        "src/prompts.py",
        "src/__init__.py",
        "examples/generate.py",
        "requirements.txt",
        "README.md"
    }
    
    REQUIRED_DIRS = {
        "src",
        "examples",
        "core"
    }
    
    def validate(self, extracted_path: Path) -> StepResult:
        """Validate file structure"""
        issues: List[Issue] = []
        
        # Check required directories
        for dir_name in self.REQUIRED_DIRS:
            dir_path = extracted_path / dir_name
            if not dir_path.exists():
                issues.append(Issue(
                    step="structure",
                    severity=Severity.CRITICAL,
                    message=f"Missing required directory: {dir_name}",
                    file_path=str(dir_path)
                ))
        
        # Check required files
        for file_path in self.REQUIRED_FILES:
            full_path = extracted_path / file_path
            if not full_path.exists():
                issues.append(Issue(
                    step="structure",
                    severity=Severity.CRITICAL,
                    message=f"Missing required file: {file_path}",
                    file_path=str(full_path)
                ))
            elif full_path.stat().st_size == 0:
                issues.append(Issue(
                    step="structure",
                    severity=Severity.WARNING,
                    message=f"File is empty: {file_path}",
                    file_path=str(full_path)
                ))
        
        # Check for template residue
        self._check_template_residue(extracted_path, issues)
        
        # Check entry point is executable
        generate_script = extracted_path / "examples/generate.py"
        if generate_script.exists():
            content = generate_script.read_text()
            if "if __name__" not in content:
                issues.append(Issue(
                    step="structure",
                    severity=Severity.WARNING,
                    message="generate.py missing __main__ entry point",
                    file_path=str(generate_script)
                ))
        
        return StepResult(
            step_name="File Structure Check",
            passed=len([i for i in issues if i.severity == Severity.CRITICAL]) == 0,
            issues=issues,
            details={
                "required_files_found": len(self.REQUIRED_FILES) - len([i for i in issues if "Missing required file" in i.message]),
                "required_dirs_found": len(self.REQUIRED_DIRS) - len([i for i in issues if "Missing required directory" in i.message])
            }
        )
    
    def _check_template_residue(self, extracted_path: Path, issues: List[Issue]):
        """Check for leftover template content"""
        template_keywords = ["chess", "ChessGenerator", "chess_task"]
        
        for py_file in extracted_path.rglob("*.py"):
            if py_file.name.startswith("."):
                continue
            
            content = py_file.read_text(errors="ignore")
            for keyword in template_keywords:
                if keyword in content:
                    issues.append(Issue(
                        step="structure",
                        severity=Severity.WARNING,
                        message=f"Template keyword '{keyword}' found in code",
                        details="May contain residual template content",
                        file_path=str(py_file.relative_to(extracted_path))
                    ))
                    break
