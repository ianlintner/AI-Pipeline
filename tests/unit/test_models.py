import pytest
from datetime import datetime
from pydantic import ValidationError
from models import (
    BugReport,
    TriageResult,
    GitHubIssue,
    TicketCreationRequest,
    RequestState,
    StatusUpdate,
    Priority,
    Severity,
    TicketStatus,
)


class TestBugReport:
    """Test BugReport model"""

    def test_bug_report_creation_valid(self):
        """Test creating a valid bug report"""
        bug_report = BugReport(
            id="BUG-001",
            title="Test Bug",
            description="Test description",
            reporter="test@example.com",
        )

        assert bug_report.id == "BUG-001"
        assert bug_report.title == "Test Bug"
        assert bug_report.description == "Test description"
        assert bug_report.reporter == "test@example.com"
        assert bug_report.attachments == []
        assert bug_report.metadata == {}
        assert isinstance(bug_report.created_at, datetime)

    def test_bug_report_creation_with_optional_fields(self):
        """Test creating bug report with all optional fields"""
        bug_report = BugReport(
            id="BUG-002",
            title="Complex Bug",
            description="Detailed description",
            reporter="user@example.com",
            environment="Production",
            steps_to_reproduce="1. Step one\n2. Step two",
            expected_behavior="Should work",
            actual_behavior="Doesn't work",
            attachments=["file1.log", "screenshot.png"],
            metadata={"priority": "high"},
        )

        assert bug_report.environment == "Production"
        assert bug_report.steps_to_reproduce == "1. Step one\n2. Step two"
        assert bug_report.expected_behavior == "Should work"
        assert bug_report.actual_behavior == "Doesn't work"
        assert bug_report.attachments == ["file1.log", "screenshot.png"]
        assert bug_report.metadata == {"priority": "high"}

    def test_bug_report_missing_required_fields(self):
        """Test validation error when required fields are missing"""
        with pytest.raises(ValidationError):
            BugReport(
                title="Missing ID",
                description="Test description",
                reporter="test@example.com",
            )

        with pytest.raises(ValidationError):
            BugReport(
                id="BUG-003", description="Missing title", reporter="test@example.com"
            )


class TestTriageResult:
    """Test TriageResult model"""

    def test_triage_result_creation_valid(self):
        """Test creating a valid triage result"""
        triage_result = TriageResult(
            bug_report_id="BUG-001",
            priority=Priority.HIGH,
            severity=Severity.MAJOR,
            category="frontend",
            triage_notes="Critical issue",
        )

        assert triage_result.bug_report_id == "BUG-001"
        assert triage_result.priority == Priority.HIGH
        assert triage_result.severity == Severity.MAJOR
        assert triage_result.category == "frontend"
        assert triage_result.triage_notes == "Critical issue"
        assert triage_result.labels == []
        assert triage_result.assignee_suggestion is None
        assert isinstance(triage_result.created_at, datetime)

    def test_triage_result_with_all_fields(self):
        """Test triage result with all optional fields"""
        triage_result = TriageResult(
            bug_report_id="BUG-002",
            priority=Priority.CRITICAL,
            severity=Severity.BLOCKER,
            category="backend",
            labels=["bug", "critical", "database"],
            assignee_suggestion="backend-team",
            duplicate_of="BUG-001",
            triage_notes="Duplicate of existing issue",
            estimated_effort="large",
        )

        assert triage_result.labels == ["bug", "critical", "database"]
        assert triage_result.assignee_suggestion == "backend-team"
        assert triage_result.duplicate_of == "BUG-001"
        assert triage_result.estimated_effort == "large"

    def test_priority_enum_values(self):
        """Test priority enum values"""
        assert Priority.LOW == "low"
        assert Priority.MEDIUM == "medium"
        assert Priority.HIGH == "high"
        assert Priority.CRITICAL == "critical"

    def test_severity_enum_values(self):
        """Test severity enum values"""
        assert Severity.MINOR == "minor"
        assert Severity.MODERATE == "moderate"
        assert Severity.MAJOR == "major"
        assert Severity.BLOCKER == "blocker"


class TestGitHubIssue:
    """Test GitHubIssue model"""

    def test_github_issue_creation_minimal(self):
        """Test creating GitHub issue with minimal fields"""
        issue = GitHubIssue(title="Bug Title", body="Bug description")

        assert issue.title == "Bug Title"
        assert issue.body == "Bug description"
        assert issue.labels == []
        assert issue.assignees == []
        assert issue.milestone is None

    def test_github_issue_creation_full(self):
        """Test creating GitHub issue with all fields"""
        issue = GitHubIssue(
            title="Complex Bug",
            body="Detailed description",
            labels=["bug", "high-priority"],
            assignees=["developer1", "developer2"],
            milestone="v1.0",
        )

        assert issue.title == "Complex Bug"
        assert issue.body == "Detailed description"
        assert issue.labels == ["bug", "high-priority"]
        assert issue.assignees == ["developer1", "developer2"]
        assert issue.milestone == "v1.0"


class TestRequestState:
    """Test RequestState model"""

    def test_request_state_creation(self):
        """Test creating request state"""
        state = RequestState(
            request_id="req-123",
            bug_report_id="BUG-001",
            status=TicketStatus.PENDING,
            current_step="triage",
        )

        assert state.request_id == "req-123"
        assert state.bug_report_id == "BUG-001"
        assert state.status == TicketStatus.PENDING
        assert state.current_step == "triage"
        assert state.progress == {}
        assert state.error_message is None
        assert state.github_issue_number is None
        assert state.github_issue_url is None
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.updated_at, datetime)

    def test_ticket_status_enum_values(self):
        """Test ticket status enum values"""
        assert TicketStatus.PENDING == "pending"
        assert TicketStatus.TRIAGED == "triaged"
        assert TicketStatus.IN_PROGRESS == "in_progress"
        assert TicketStatus.CREATED == "created"
        assert TicketStatus.FAILED == "failed"


class TestStatusUpdate:
    """Test StatusUpdate model"""

    def test_status_update_creation(self):
        """Test creating status update"""
        update = StatusUpdate(
            request_id="req-123",
            status=TicketStatus.TRIAGED,
            message="Triage completed successfully",
        )

        assert update.request_id == "req-123"
        assert update.status == TicketStatus.TRIAGED
        assert update.message == "Triage completed successfully"
        assert update.metadata == {}
        assert isinstance(update.timestamp, datetime)


class TestTicketCreationRequest:
    """Test TicketCreationRequest model"""

    def test_ticket_creation_request(self, sample_bug_report, sample_triage_result):
        """Test creating ticket creation request"""
        github_issue = GitHubIssue(title="Test Issue", body="Test body")

        request = TicketCreationRequest(
            bug_report=sample_bug_report,
            triage_result=sample_triage_result,
            github_issue=github_issue,
            request_id="req-123",
        )

        assert request.bug_report == sample_bug_report
        assert request.triage_result == sample_triage_result
        assert request.github_issue == github_issue
        assert request.request_id == "req-123"
        assert isinstance(request.created_at, datetime)
