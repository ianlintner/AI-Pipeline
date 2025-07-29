import pytest
import fakeredis
from unittest.mock import Mock, patch
from datetime import datetime
from models import BugReport, TriageResult, Priority, Severity, TicketStatus
from config import Config

@pytest.fixture
def sample_bug_report():
    """Sample bug report for testing"""
    return BugReport(
        id="BUG-001",
        title="Login page crashes on mobile devices",
        description="The login page consistently crashes when accessed from mobile browsers.",
        reporter="test@example.com",
        environment="Mobile browsers (iOS Safari, Android Chrome)",
        steps_to_reproduce="1. Open app on mobile\n2. Navigate to login\n3. App crashes",
        expected_behavior="Login should work normally",
        actual_behavior="Page crashes with JavaScript error",
        attachments=["screenshot.png"],
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        metadata={"severity": "high", "browser": "safari"}
    )

@pytest.fixture
def sample_triage_result():
    """Sample triage result for testing"""
    return TriageResult(
        bug_report_id="BUG-001",
        priority=Priority.HIGH,
        severity=Severity.MAJOR,
        category="frontend",
        labels=["bug", "mobile", "crash"],
        assignee_suggestion="frontend-team",
        triage_notes="Critical mobile issue affecting user login",
        estimated_effort="medium",
        created_at=datetime(2024, 1, 1, 12, 5, 0)
    )

@pytest.fixture
def mock_redis():
    """Mock Redis client using fakeredis"""
    return fakeredis.FakeStrictRedis(decode_responses=True)

@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer"""
    mock_producer = Mock()
    mock_producer.send.return_value = Mock()
    mock_producer.flush.return_value = None
    return mock_producer

@pytest.fixture
def mock_kafka_consumer():
    """Mock Kafka consumer"""
    mock_consumer = Mock()
    mock_consumer.poll.return_value = {}
    mock_consumer.commit.return_value = None
    mock_consumer.close.return_value = None
    return mock_consumer

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    mock_client = Mock()
    
    # Mock chat completion response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = '{"priority": "high", "severity": "major", "category": "frontend"}'
    
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

@pytest.fixture
def mock_github_client():
    """Mock GitHub client"""
    mock_client = Mock()
    
    # Mock issue creation response
    mock_issue = Mock()
    mock_issue.number = 1234
    mock_issue.html_url = "https://github.com/test/repo/issues/1234"
    
    mock_client.get_repo.return_value.create_issue.return_value = mock_issue
    return mock_client

@pytest.fixture
def test_config():
    """Test configuration override"""
    original_values = {}
    
    # Store original values
    original_values['KAFKA_BOOTSTRAP_SERVERS'] = Config.KAFKA_BOOTSTRAP_SERVERS
    original_values['REDIS_URL'] = Config.REDIS_URL
    original_values['OPENAI_API_KEY'] = Config.OPENAI_API_KEY
    
    # Set test values
    Config.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    Config.REDIS_URL = "redis://localhost:6379"
    Config.OPENAI_API_KEY = "test-key"
    
    yield Config
    
    # Restore original values
    for key, value in original_values.items():
        setattr(Config, key, value)

@pytest.fixture
def mock_state_manager(mock_redis):
    """Mock state manager with fake Redis"""
    with patch('state_manager.StateManager') as mock_sm:
        mock_instance = Mock()
        mock_instance.redis_client = mock_redis
        mock_instance.save_request_state.return_value = True
        mock_instance.get_request_state.return_value = None
        mock_instance.update_request_status.return_value = True
        mock_instance.get_all_active_requests.return_value = []
        mock_sm.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_agents():
    """Mock all agent types"""
    agents = {}
    
    # Mock TriageAgent
    agents['triage'] = Mock()
    agents['triage'].agent_name = "TriageAgent"
    agents['triage'].process_message.return_value = None
    agents['triage'].cleanup.return_value = None
    
    # Mock TicketCreationAgent
    agents['ticket_creation'] = Mock()
    agents['ticket_creation'].agent_name = "TicketCreationAgent"
    agents['ticket_creation'].process_message.return_value = None
    agents['ticket_creation'].cleanup.return_value = None
    
    # Mock GitHubAPIAgent
    agents['github_api'] = Mock()
    agents['github_api'].agent_name = "GitHubAPIAgent"
    agents['github_api'].process_message.return_value = None
    agents['github_api'].cleanup.return_value = None
    
    # Mock CoordinatorAgent
    agents['coordinator'] = Mock()
    agents['coordinator'].agent_name = "CoordinatorAgent"
    agents['coordinator'].process_message.return_value = None
    agents['coordinator'].cleanup.return_value = None
    agents['coordinator'].submit_bug_report.return_value = "test-request-id"
    agents['coordinator'].get_request_status.return_value = {
        "status": "pending",
        "current_step": "triage"
    }
    agents['coordinator'].get_all_active_requests.return_value = []
    agents['coordinator'].start_monitoring.return_value = None
    agents['coordinator'].stop_monitoring.return_value = None
    agents['coordinator'].active_requests = {}
    
    return agents

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables for each test"""
    import os
    
    # Store original env vars
    original_env = {}
    test_env_vars = [
        'OPENAI_API_KEY',
        'GITHUB_API_TOKEN',
        'KAFKA_BOOTSTRAP_SERVERS',
        'REDIS_URL'
    ]
    
    for var in test_env_vars:
        original_env[var] = os.environ.get(var)
        os.environ[var] = f"test-{var.lower()}"
    
    yield
    
    # Restore original env vars
    for var, value in original_env.items():
        if value is None:
            os.environ.pop(var, None)
        else:
            os.environ[var] = value
