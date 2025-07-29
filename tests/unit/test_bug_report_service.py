from unittest.mock import MagicMock, Mock, patch

import pytest

from bug_report_service import BugReportTriageService
from models import BugReport, TicketStatus


class TestBugReportTriageService:
    """Test BugReportTriageService"""

    @pytest.fixture
    def service(self, mock_agents):
        """Create service instance with mocked dependencies"""
        with (
            patch("bug_report_service.TriageAgent") as mock_triage,
            patch("bug_report_service.TicketCreationAgent") as mock_ticket,
            patch("bug_report_service.GitHubAPIAgent") as mock_github,
            patch("bug_report_service.CoordinatorAgent") as mock_coord,
            patch("bug_report_service.KafkaConsumerManager") as mock_consumer,
        ):

            mock_triage.return_value = mock_agents["triage"]
            mock_ticket.return_value = mock_agents["ticket_creation"]
            mock_github.return_value = mock_agents["github_api"]
            mock_coord.return_value = mock_agents["coordinator"]
            mock_consumer.return_value = Mock()

            service = BugReportTriageService()
            yield service

    def test_initialization(self, service):
        """Test service initialization"""
        assert service.agents == {}
        assert service.consumers == {}
        assert service.coordinator is not None
        assert service.running == False

    def test_initialize_agents(self, service, mock_agents):
        """Test agent initialization"""
        service.coordinator = mock_agents["coordinator"]
        service.initialize_agents()

        assert "triage" in service.agents
        assert "ticket_creation" in service.agents
        assert "github_api" in service.agents
        assert "coordinator" in service.agents
        assert service.agents["coordinator"] == mock_agents["coordinator"]

    @patch("bug_report_service.KafkaConsumerManager")
    def test_initialize_consumers(self, mock_consumer_class, service):
        """Test Kafka consumer initialization"""
        mock_consumer = Mock()
        mock_consumer_class.return_value = mock_consumer

        service.agents = {
            "triage": Mock(),
            "ticket_creation": Mock(),
            "github_api": Mock(),
            "coordinator": Mock(),
        }

        service.initialize_consumers()

        assert len(service.consumers) == 4
        assert "triage" in service.consumers
        assert "ticket_creation" in service.consumers
        assert "github_api" in service.consumers
        assert "coordinator" in service.consumers

        # Verify consumer was created with correct parameters
        assert mock_consumer_class.call_count == 4

    @patch("bug_report_service.threading.Thread")
    @patch("bug_report_service.threading.Event")
    def test_start_service(self, mock_event_class, mock_thread, service):
        """Test starting the service"""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        # Mock the initialize methods
        service.initialize_agents = Mock()
        service.initialize_consumers = Mock()
        service.coordinator = Mock()
        service.consumers = {"test": Mock()}

        # Mock threading.Event to raise KeyboardInterrupt on wait
        mock_event_instance = Mock()
        mock_event_class.return_value = mock_event_instance
        mock_event_instance.wait.side_effect = KeyboardInterrupt()

        # The KeyboardInterrupt should be caught and handled gracefully
        service.start_service()

        # Verify initialization was called
        service.initialize_agents.assert_called_once()
        service.initialize_consumers.assert_called_once()
        service.coordinator.start_monitoring.assert_called_once()

        # Verify thread was started
        mock_thread_instance.start.assert_called()
        assert service.running == True

    def test_stop_service(self, service):
        """Test stopping the service"""
        # Setup mocks
        mock_consumer = Mock()
        mock_agent = Mock()

        service.consumers = {"test_consumer": mock_consumer}
        service.agents = {"test_agent": mock_agent}
        service.coordinator = Mock()
        service.running = True

        service.stop_service()

        # Verify cleanup was called
        mock_consumer.stop_consuming.assert_called_once()
        mock_agent.cleanup.assert_called_once()
        service.coordinator.stop_monitoring.assert_called_once()
        assert service.running == False

    def test_stop_service_with_exceptions(self, service):
        """Test stopping service handles exceptions gracefully"""
        # Setup mocks that raise exceptions
        mock_consumer = Mock()
        mock_consumer.stop_consuming.side_effect = Exception("Consumer error")

        mock_agent = Mock()
        mock_agent.cleanup.side_effect = Exception("Agent error")

        service.consumers = {"test_consumer": mock_consumer}
        service.agents = {"test_agent": mock_agent}
        service.coordinator = Mock()
        service.running = True

        # Should not raise exception
        service.stop_service()

        assert service.running == False

    def test_submit_bug_report_success(self, service, sample_bug_report):
        """Test successful bug report submission"""
        service.running = True
        service.coordinator = Mock()
        service.coordinator.submit_bug_report.return_value = "test-request-id"

        request_id = service.submit_bug_report(sample_bug_report)

        assert request_id == "test-request-id"
        service.coordinator.submit_bug_report.assert_called_once_with(sample_bug_report)

    def test_submit_bug_report_service_not_running(self, service, sample_bug_report):
        """Test bug report submission when service is not running"""
        service.running = False

        request_id = service.submit_bug_report(sample_bug_report)

        assert request_id is None

    def test_submit_bug_report_exception(self, service, sample_bug_report):
        """Test bug report submission handles exceptions"""
        service.running = True
        service.coordinator = Mock()
        service.coordinator.submit_bug_report.side_effect = Exception("Submit error")

        request_id = service.submit_bug_report(sample_bug_report)

        assert request_id is None

    def test_get_request_status_success(self, service):
        """Test successful request status retrieval"""
        service.coordinator = Mock()
        expected_status = {"status": "pending", "current_step": "triage"}
        service.coordinator.get_request_status.return_value = expected_status

        status = service.get_request_status("test-request-id")

        assert status == expected_status
        service.coordinator.get_request_status.assert_called_once_with(
            "test-request-id"
        )

    def test_get_request_status_exception(self, service):
        """Test request status retrieval handles exceptions"""
        service.coordinator = Mock()
        service.coordinator.get_request_status.side_effect = Exception("Status error")

        status = service.get_request_status("test-request-id")

        assert status is None

    def test_get_all_active_requests_success(self, service):
        """Test successful active requests retrieval"""
        service.coordinator = Mock()
        expected_requests = [{"request_id": "req-1", "status": "pending"}]
        service.coordinator.get_all_active_requests.return_value = expected_requests

        requests = service.get_all_active_requests()

        assert requests == expected_requests
        service.coordinator.get_all_active_requests.assert_called_once()

    def test_get_all_active_requests_exception(self, service):
        """Test active requests retrieval handles exceptions"""
        service.coordinator = Mock()
        service.coordinator.get_all_active_requests.side_effect = Exception(
            "Requests error"
        )

        requests = service.get_all_active_requests()

        assert requests == []

    def test_health_check_healthy(self, service):
        """Test health check when service is healthy"""
        service.running = True
        service.agents = {
            "triage": Mock(agent_name="TriageAgent"),
            "coordinator": Mock(agent_name="CoordinatorAgent"),
        }
        service.consumers = {"triage": Mock(), "coordinator": Mock()}
        service.coordinator = Mock()
        service.coordinator.active_requests = {"req-1": Mock()}

        health = service.health_check()

        assert health["service_running"] == True
        assert health["agents_count"] == 2
        assert health["consumers_count"] == 2
        assert health["active_requests"] == 1
        assert health["overall_status"] == "healthy"
        assert "components" in health
        assert health["components"]["triage_agent"]["status"] == "healthy"
        assert health["components"]["coordinator_agent"]["status"] == "healthy"

    def test_health_check_unhealthy(self, service):
        """Test health check when service is unhealthy"""
        service.running = False
        service.agents = {}
        service.consumers = {}
        service.coordinator = None

        health = service.health_check()

        assert health["service_running"] == False
        assert health["agents_count"] == 0
        assert health["consumers_count"] == 0
        assert health["active_requests"] == 0
        assert health["overall_status"] == "unhealthy"

    def test_health_check_agent_exception(self, service):
        """Test health check handles agent exceptions"""
        service.running = True

        # Create mock agent that raises exception when accessing agent_name
        mock_agent = Mock()
        del mock_agent.agent_name  # Remove agent_name attribute

        service.agents = {"problematic": mock_agent}
        service.consumers = {}
        service.coordinator = Mock()
        service.coordinator.active_requests = {}

        health = service.health_check()

        assert health["overall_status"] == "healthy"  # Service still running
        assert health["components"]["problematic_agent"]["status"] == "unhealthy"

    def test_health_check_exception(self, service):
        """Test health check handles general exceptions"""
        service.running = True
        service.agents = None  # This will cause an exception

        health = service.health_check()

        assert health["overall_status"] == "unhealthy"
        assert "error" in health

    @patch("signal.signal")
    @patch("bug_report_service.CoordinatorAgent")
    def test_signal_handler_setup(self, mock_coordinator, mock_signal):
        """Test signal handlers are set up during initialization"""
        mock_coordinator.return_value = Mock()
        service = BugReportTriageService()

        # Verify signal handlers were registered
        assert mock_signal.call_count >= 2

    def test_signal_handler(self, service):
        """Test signal handler stops service and exits"""
        service.stop_service = Mock()

        with patch("sys.exit") as mock_exit:
            service._signal_handler(2, None)  # SIGINT

            service.stop_service.assert_called_once()
            mock_exit.assert_called_once_with(0)
