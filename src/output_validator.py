"""Output format validation by running the generator"""

import subprocess
import sys
import shutil
from pathlib import Path
from typing import List, Optional
from .models import Issue, Severity, StepResult


class OutputValidator:
    """Validates generator output by running it in isolated environment"""
    
    REQUIRED_OUTPUT_FILES = {
        "first_frame.png",
        "prompt.txt"
    }
    
    OPTIONAL_OUTPUT_FILES = {
        "final_frame.png",
        "ground_truth.mp4",
        "goal.txt"
    }
    
    def validate(self, extracted_path: Path, domain: Optional[str], num_samples: int = 5) -> StepResult:
        """Run generator and validate output"""
        issues: List[Issue] = []
        
        # Create isolated virtual environment
        venv_path = extracted_path / ".test_venv"
        venv_created = self._create_venv(extracted_path, venv_path, issues)
        
        if not venv_created:
            return StepResult(
                step_name="Output Format Check",
                passed=False,
                issues=issues,
                details={"generated_samples": 0}
            )
        
        # Run generator in isolated environment
        run_success = self._run_generator_isolated(extracted_path, venv_path, num_samples, issues)
        
        if not run_success:
            return StepResult(
                step_name="Output Format Check",
                passed=False,
                issues=issues,
                details={"generated_samples": 0}
            )
        
        # Find output directory
        output_dir = self._find_output_dir(extracted_path, domain)
        if not output_dir:
            issues.append(Issue(
                step="output",
                severity=Severity.CRITICAL,
                message="Could not find output directory",
                details=f"Expected: data/questions/{domain}_task/ or data/{domain}_task/"
            ))
            return StepResult(
                step_name="Output Format Check",
                passed=False,
                issues=issues,
                details={"generated_samples": 0}
            )
        
        # Validate output structure
        task_dirs = self._validate_output_structure(output_dir, domain, num_samples, issues)
        
        # Cleanup venv
        if venv_path.exists():
            shutil.rmtree(venv_path, ignore_errors=True)
        
        return StepResult(
            step_name="Output Format Check",
            passed=len([i for i in issues if i.severity == Severity.CRITICAL]) == 0,
            issues=issues,
            details={
                "generated_samples": len(task_dirs),
                "output_directory": str(output_dir)
            }
        )
    
    def _create_venv(self, extracted_path: Path, venv_path: Path, issues: List[Issue]) -> bool:
        """Create isolated virtual environment for testing"""
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            cwd=extracted_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            issues.append(Issue(
                step="output",
                severity=Severity.CRITICAL,
                message="Failed to create test virtual environment",
                details=result.stderr[:500]
            ))
            return False
        
        return True
    
    def _get_venv_python(self, venv_path: Path) -> str:
        """Get python executable path from venv"""
        if sys.platform == "win32":
            return str(venv_path / "Scripts" / "python.exe")
        return str(venv_path / "bin" / "python")
    
    def _run_generator_isolated(self, extracted_path: Path, venv_path: Path, num_samples: int, issues: List[Issue]) -> bool:
        """Run the generator script in isolated subprocess"""
        generate_script = extracted_path / "examples/generate.py"
        
        if not generate_script.exists():
            issues.append(Issue(
                step="output",
                severity=Severity.CRITICAL,
                message="Cannot run generator - examples/generate.py not found"
            ))
            return False
        
        python_exe = self._get_venv_python(venv_path)
        
        # Install dependencies in isolated venv
        req_file = extracted_path / "requirements.txt"
        if req_file.exists():
            install_result = subprocess.run(
                [python_exe, "-m", "pip", "install", "--quiet", "-r", str(req_file)],
                cwd=extracted_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if install_result.returncode != 0:
                issues.append(Issue(
                    step="output",
                    severity=Severity.CRITICAL,
                    message="Failed to install dependencies in isolated environment",
                    details=install_result.stderr[:500]
                ))
                return False
        
        # Install generator package if setup.py exists
        setup_file = extracted_path / "setup.py"
        if setup_file.exists():
            setup_result = subprocess.run(
                [python_exe, "-m", "pip", "install", "--quiet", "-e", "."],
                cwd=extracted_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if setup_result.returncode != 0:
                issues.append(Issue(
                    step="output",
                    severity=Severity.WARNING,
                    message="Failed to install generator package (setup.py)",
                    details=setup_result.stderr[:300]
                ))
        
        # Run generator in isolated subprocess
        result = subprocess.run(
            [python_exe, str(generate_script), "--num-samples", str(num_samples)],
            cwd=extracted_path,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            issues.append(Issue(
                step="output",
                severity=Severity.CRITICAL,
                message="Generator execution failed",
                details=f"Exit code: {result.returncode}\n{result.stderr[:500]}"
            ))
            return False
        
        return True
    
    def _find_output_dir(self, extracted_path: Path, domain: Optional[str]) -> Optional[Path]:
        """Find the output directory"""
        # Try standard locations
        possible_paths = [
            extracted_path / "data/questions" / f"{domain}_task" if domain else None,
            extracted_path / "data" / f"{domain}_task" if domain else None,
            extracted_path / "data/questions",
            extracted_path / "data"
        ]
        
        for path in possible_paths:
            if path and path.exists() and any(path.iterdir()):
                # If it's a parent dir, find the actual task dir
                if path.name in ["questions", "data"]:
                    task_dirs = [d for d in path.iterdir() if d.is_dir() and "_task" in d.name]
                    if task_dirs:
                        return task_dirs[0]
                return path
        
        return None
    
    def _validate_output_structure(
        self, 
        output_dir: Path, 
        domain: Optional[str],
        expected_samples: int,
        issues: List[Issue]
    ) -> List[Path]:
        """Validate the structure of generated output"""
        task_dirs = sorted([d for d in output_dir.iterdir() if d.is_dir()])
        
        if len(task_dirs) == 0:
            issues.append(Issue(
                step="output",
                severity=Severity.CRITICAL,
                message="No task directories generated",
                file_path=str(output_dir)
            ))
            return []
        
        if len(task_dirs) != expected_samples:
            issues.append(Issue(
                step="output",
                severity=Severity.WARNING,
                message=f"Expected {expected_samples} samples, got {len(task_dirs)}",
                file_path=str(output_dir)
            ))
        
        # Check first few task directories
        for task_dir in task_dirs[:min(5, len(task_dirs))]:
            self._validate_task_directory(task_dir, domain, issues)
        
        return task_dirs
    
    def _validate_task_directory(self, task_dir: Path, domain: Optional[str], issues: List[Issue]):
        """Validate a single task directory"""
        task_id = task_dir.name
        
        # Validate task_id format
        if domain and not task_id.startswith(f"{domain}_"):
            issues.append(Issue(
                step="output",
                severity=Severity.CRITICAL,
                message=f"Task ID doesn't match domain: {task_id}",
                details=f"Should start with '{domain}_'",
                file_path=str(task_dir)
            ))
        
        # Check for proper numbering (e.g., task_0000, task_0001)
        if domain and not task_id.replace(f"{domain}_", "").isdigit():
            issues.append(Issue(
                step="output",
                severity=Severity.WARNING,
                message=f"Task ID has non-standard format: {task_id}",
                details="Expected format: {domain}_0000, {domain}_0001, etc.",
                file_path=str(task_dir)
            ))
        
        # Check required files
        for required_file in self.REQUIRED_OUTPUT_FILES:
            file_path = task_dir / required_file
            if not file_path.exists():
                issues.append(Issue(
                    step="output",
                    severity=Severity.CRITICAL,
                    message=f"Missing required file: {required_file}",
                    file_path=str(task_dir)
                ))
            elif file_path.stat().st_size == 0:
                issues.append(Issue(
                    step="output",
                    severity=Severity.CRITICAL,
                    message=f"Empty file: {required_file}",
                    file_path=str(file_path)
                ))
        
        # Check for at least one goal indicator
        has_final_frame = (task_dir / "final_frame.png").exists()
        has_goal_txt = (task_dir / "goal.txt").exists()
        
        if not has_final_frame and not has_goal_txt:
            issues.append(Issue(
                step="output",
                severity=Severity.WARNING,
                message="No goal indicator found",
                details="Should have either final_frame.png or goal.txt",
                file_path=str(task_dir)
            ))
        
        # Check video if present
        video_path = task_dir / "ground_truth.mp4"
        if video_path.exists():
            self._validate_video(video_path, issues)
        
        # Check prompt length
        prompt_path = task_dir / "prompt.txt"
        if prompt_path.exists():
            prompt_text = prompt_path.read_text()
            word_count = len(prompt_text.split())
            if word_count > 200:
                issues.append(Issue(
                    step="output",
                    severity=Severity.WARNING,
                    message=f"Prompt too long: {word_count} words (max 200)",
                    file_path=str(prompt_path)
                ))
    
    def _validate_video(self, video_path: Path, issues: List[Issue]):
        """Validate video file"""
        try:
            import cv2
            
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                issues.append(Issue(
                    step="output",
                    severity=Severity.CRITICAL,
                    message="Cannot open video file",
                    file_path=str(video_path)
                ))
                return
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            if duration > 10.5:
                issues.append(Issue(
                    step="output",
                    severity=Severity.WARNING,
                    message=f"Video too long: {duration:.1f}s (max 10s)",
                    file_path=str(video_path)
                ))
            
            if frame_count == 0:
                issues.append(Issue(
                    step="output",
                    severity=Severity.CRITICAL,
                    message="Video has no frames",
                    file_path=str(video_path)
                ))
        
        except Exception as e:
            issues.append(Issue(
                step="output",
                severity=Severity.WARNING,
                message=f"Could not validate video: {str(e)}",
                file_path=str(video_path)
            ))
