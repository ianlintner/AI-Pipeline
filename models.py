from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Severity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    BLOCKER = "blocker"


class TicketStatus(str, Enum):
    PENDING = "pending"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    CREATED = "created"
    FAILED = "failed"


class BugReport(BaseModel):
    id: str = Field(..., description="Unique identifier for the bug report")
    title: str = Field(..., description="Title of the bug report")
    description: str = Field(..., description="Detailed description of the bug")
    reporter: str = Field(
        ..., description="Name or email of the person reporting the bug"
    )
    environment: Optional[str] = Field(
        None, description="Environment where bug occurred"
    )
    steps_to_reproduce: Optional[str] = Field(
        None, description="Steps to reproduce the bug"
    )
    expected_behavior: Optional[str] = Field(None, description="Expected behavior")
    actual_behavior: Optional[str] = Field(None, description="Actual behavior observed")
    attachments: Optional[List[str]] = Field(
        default_factory=list, description="List of attachment URLs"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TriageResult(BaseModel):
    bug_report_id: str
    priority: Priority
    severity: Severity
    category: str = Field(
        ..., description="Category of the bug (e.g., 'frontend', 'backend', 'database')"
    )
    labels: List[str] = Field(
        default_factory=list, description="Labels to be applied to GitHub issue"
    )
    assignee_suggestion: Optional[str] = Field(None, description="Suggested assignee")
    duplicate_of: Optional[str] = Field(
        None, description="ID of duplicate issue if applicable"
    )
    triage_notes: str = Field(..., description="Notes from the triage process")
    estimated_effort: Optional[str] = Field(None, description="Estimated effort to fix")
    created_at: datetime = Field(default_factory=datetime.now)


class GitHubIssue(BaseModel):
    title: str
    body: str
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    milestone: Optional[str] = None


class TicketCreationRequest(BaseModel):
    bug_report: BugReport
    triage_result: TriageResult
    github_issue: GitHubIssue
    request_id: str
    created_at: datetime = Field(default_factory=datetime.now)


class RequestState(BaseModel):
    request_id: str
    bug_report_id: str
    status: TicketStatus
    current_step: str
    progress: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    github_issue_number: Optional[int] = None
    github_issue_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class StatusUpdate(BaseModel):
    request_id: str
    status: TicketStatus
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
