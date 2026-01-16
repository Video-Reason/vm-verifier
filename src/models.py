"""Pydantic models for verification results"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Issue(BaseModel):
    """A single verification issue"""
    step: str = Field(description="Verification step name")
    severity: Severity
    message: str
    details: Optional[str] = None
    file_path: Optional[str] = None


class StepResult(BaseModel):
    """Result from a single verification step"""
    step_name: str
    passed: bool
    issues: List[Issue] = Field(default_factory=list)
    details: dict = Field(default_factory=dict)


class VerificationResult(BaseModel):
    """Complete verification result"""
    generator_path: str
    domain: Optional[str] = None
    passed: bool
    steps: List[StepResult] = Field(default_factory=list)
    
    @property
    def total_issues(self) -> int:
        return sum(len(step.issues) for step in self.steps)
    
    @property
    def critical_issues(self) -> int:
        return sum(
            sum(1 for issue in step.issues if issue.severity == Severity.CRITICAL)
            for step in self.steps
        )
    
    @property
    def warning_issues(self) -> int:
        return sum(
            sum(1 for issue in step.issues if issue.severity == Severity.WARNING)
            for step in self.steps
        )
