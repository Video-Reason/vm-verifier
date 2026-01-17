"""Main verification engine orchestrator"""

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from .models import Issue, Severity, StepResult, VerificationResult
from .structure_validator import StructureValidator
from .format_validator import FormatValidator
from .output_validator import OutputValidator


class VerificationEngine:
    """Main verification orchestrator"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.structure_validator = StructureValidator()
        self.format_validator = FormatValidator()
        self.output_validator = OutputValidator()
    
    def verify(self, zip_path: Path, num_samples: int = 5) -> VerificationResult:
        """Run complete verification pipeline"""
        temp_dir = None
        
        self._log(f"📦 Extracting generator: {zip_path.name}")
        
        # Extract to temp directory
        temp_dir = Path(tempfile.mkdtemp(prefix="vm_verify_"))
        extracted_path = self._extract_zip(zip_path, temp_dir)
        
        if not extracted_path:
            return VerificationResult(
                generator_path=str(zip_path),
                passed=False,
                steps=[StepResult(
                    step_name="Extraction",
                    passed=False,
                    issues=[Issue(
                        step="extraction",
                        severity=Severity.CRITICAL,
                        message="Failed to extract zip file"
                    )]
                )]
            )
        
        results = []
        domain = None
        
        # Step 1: File Structure Check
        self._log("\n📁 Step 1: Checking file structure...")
        structure_result = self.structure_validator.validate(extracted_path)
        results.append(structure_result)
        self._print_step_result(structure_result)
        
        # Step 2: Code Format Check
        self._log("\n🔤 Step 2: Checking code format and naming...")
        format_result = self.format_validator.validate(extracted_path)
        results.append(format_result)
        domain = format_result.details.get("domain")
        self._print_step_result(format_result)
        
        # Step 3: Output Format Check (run generator)
        if structure_result.passed and format_result.passed:
            self._log(f"\n▶️  Step 3: Running generator ({num_samples} samples)...")
            output_result = self.output_validator.validate(extracted_path, domain, num_samples)
            results.append(output_result)
            self._print_step_result(output_result)
        else:
            self._log("\n⏭️  Step 3: Skipped (previous steps failed)")
            results.append(StepResult(
                step_name="Output Format Check",
                passed=False,
                issues=[Issue(
                    step="output",
                    severity=Severity.INFO,
                    message="Skipped due to previous failures"
                )]
            ))
        
        # Cleanup
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Determine overall pass/fail
        passed = all(r.passed for r in results)
        
        return VerificationResult(
            generator_path=str(zip_path),
            domain=domain,
            passed=passed,
            steps=results
        )
    
    def _extract_zip(self, zip_path: Path, target_dir: Path) -> Optional[Path]:
        """Extract zip file to target directory"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            # Find the actual extracted directory (may be nested)
            # Filter out system/hidden directories like __MACOSX, .git, __pycache__
            extracted_dirs = [
                d for d in target_dir.iterdir() 
                if d.is_dir() 
                and not d.name.startswith('.')        # Filter .git, .DS_Store, etc.
                and d.name != '__MACOSX'              # Filter macOS metadata
                and d.name != '__pycache__'           # Filter Python cache
            ]
            
            # If only one valid directory, assume it's the project root
            if len(extracted_dirs) == 1:
                return extracted_dirs[0]
            return target_dir
        
        except Exception as e:
            self._log(f"❌ Extraction failed: {e}")
            return None
    
    def _print_step_result(self, result: StepResult):
        """Print step result summary"""
        status = "✅ PASS" if result.passed else "❌ FAIL"
        self._log(f"   {status} - {len(result.issues)} issue(s)")
        
        if self.verbose and result.issues:
            for issue in result.issues:
                icon = "🔴" if issue.severity == Severity.CRITICAL else "⚠️"
                self._log(f"      {icon} {issue.message}")
                if issue.details:
                    self._log(f"         {issue.details}")
    
    def _log(self, message: str):
        """Log message"""
        print(message)
