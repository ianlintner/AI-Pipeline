import time
from unittest.mock import Mock, patch

import pytest

from bug_report_service import BugReportTriageService
from models import BugReport, Priority, Severity, TicketStatus


@pytest.mark.integration
class TestEndToEndIntegration:
    """End-to-end integration tests"""

    @pytest.fixture
    def service_with_mocks(self):
        """Create service with mocked external dependencies"""
        with (
            patch("kafka_utils.KafkaProducer") as mock_producer,
            patch("kafka_utils.KafkaConsumer") as mock_consumer,
            patch("redis.Redis") as mock_redis,
            patch("openai.OpenAI") as mock_openai,
            patch("github.Github") as mock_github,
        ):

            # Setup mocks
            mock_producer.return_value = Mock()
            mock_consumer.return_value = Mock()
            mock_redis.return_value = Mock()
            mock_openai.return_value = Mock()
            mock_github.return_value = Mock()

            service = BugReportTriageService()
            yield service

    def test_bug_report_processing_workflow(
        self, service_with_mocks, sample_bug_report
    ):
        """Test complete bug report processing workflow"""
        service = service_with_mocks

        # Mock successful processing at each stage
        with (
            patch.object(service, "initialize_agents") as mock_init_agents,
            patch.object(service, "initialize_consumers") as mock_init_consumers,
        ):

            # Initialize service
            service.initialize_agents()
            service.initialize_consumers()

            # Setup coordinator mock
            service.coordinator = Mock()
            service.coordinator.submit_bug_report.return_value = "test-request-id"
            service.coordinator.get_request_status.return_value = {
                "request_id": "test-request-id",
                "status": "created",
                "current_step": "completed",
                "github_issue_number": 123,
                "github_issue_url": "https://github.com/test/repo/issues/123",
            }

            service.running = True

            # Submit bug report
            request_id = service.submit_bug_report(sample_bug_report)
            assert request_id == "test-request-id"

            # Check status
            status = service.get_request_status(request_id)
            assert status["status"] == "created"
            assert status["github_issue_number"] == 123

            # Verify workflow calls
            service.coordinator.submit_bug_report.assert_called_once_with(
                sample_bug_report
            )
            service.coordinator.get_request_status.assert_called_once_with(request_id)

    def test_multiple_bug_reports_processing(self, service_with_mocks):
        """Test processing multiple bug reports concurrently"""
        service = service_with_mocks
        service.running = True

        # Create multiple bug reports
        bug_reports = []
        for i in range(3):
            bug_report = BugReport(
                id=f"BUG-{i:03d}",
                title=f"Test Bug {i}",
                description=f"Description for bug {i}",
                reporter=f"reporter{i}@example.com",
            )
            bug_reports.append(bug_report)

        # Mock coordinator responses
        service.coordinator = Mock()
        request_ids = [f"request-{i}" for i in range(3)]
        service.coordinator.submit_bug_report.side_effect = request_ids
        service.coordinator.get_all_active_requests.return_value = [
            {"request_id": rid, "status": "pending"} for rid in request_ids
        ]

        # Submit all bug reports
        submitted_ids = []
        for bug_report in bug_reports:
            request_id = service.submit_bug_report(bug_report)
            submitted_ids.append(request_id)

        assert submitted_ids == request_ids

        # Check all active requests
        active_requests = service.get_all_active_requests()
        assert len(active_requests) == 3
        assert all(req["status"] == "pending" for req in active_requests)

    def test_service_health_monitoring(self, service_with_mocks):
        """Test service health monitoring"""
        service = service_with_mocks

        # Test unhealthy state (not running)
        health = service.health_check()
        assert health["overall_status"] == "unhealthy"
        assert health["service_running"] == False

        # Setup running state
        service.running = True
        service.agents = {
            "triage": Mock(agent_name="TriageAgent"),
            "ticket_creation": Mock(agent_name="TicketCreationAgent"),
            "github_api": Mock(agent_name="GitHubAPIAgent"),
            "coordinator": Mock(agent_name="CoordinatorAgent"),
        }
        service.consumers = {name: Mock() for name in service.agents.keys()}
        service.coordinator = Mock()
        service.coordinator.active_requests = {}

        # Test healthy state
        health = service.health_check()
        assert health["overall_status"] == "healthy"
        assert health["service_running"] == True
        assert health["agents_count"] == 4
        assert health["consumers_count"] == 4
        assert health["active_requests"] == 0

        # Verify all components are healthy
        for agent_name in ["triage", "ticket_creation", "github_api", "coordinator"]:
            assert health["components"][f"{agent_name}_agent"]["status"] == "healthy"


@pytest.mark.integration
@pytest.mark.slow
class TestExternalIntegrations:
    """Test integrations with external services (requires test containers)"""

    def test_kafka_integration(self):
        """Test Kafka integration (requires running Kafka)"""
        # This would use testcontainers to spin up Kafka for testing
        pytest.skip("Requires Kafka test container setup")

    def test_redis_integration(self):
        """Test Redis integration (requires running Redis)"""
        # This would use testcontainers to spin up Redis for testing
        pytest.skip("Requires Redis test container setup")

    def test_github_api_integration(self):
        """Test GitHub API integration (requires valid token)"""
        # This would test actual GitHub API calls with test repository
        pytest.skip("Requires GitHub test repository setup")

    def test_openai_api_integration(self):
        """Test OpenAI API integration (requires valid API key)"""
        # This would test actual OpenAI API calls
        pytest.skip("Requires OpenAI API key setup")


@pytest.mark.integration
class TestErrorRecovery:
    """Test error recovery scenarios"""

    def test_kafka_connection_failure_recovery(self, service_with_mocks):
        """Test recovery from Kafka connection failures"""
        service = service_with_mocks

        # Simulate Kafka connection failure
        with patch("kafka_utils.KafkaConsumerManager") as mock_consumer:
            mock_consumer.side_effect = Exception("Kafka connection failed")

            # Service should handle initialization failure gracefully
            with pytest.raises(Exception):
                service.initialize_consumers()

    def test_redis_connection_failure_recovery(self, service_with_mocks):
        """Test recovery from Redis connection failures"""
        service = service_with_mocks
        service.running = True

        # Mock coordinator with Redis failure
        service.coordinator = Mock()
        service.coordinator.submit_bug_report.side_effect = Exception(
            "Redis connection failed"
        )

        bug_report = BugReport(
            id="BUG-001",
            title="Test Bug",
            description="Test description",
            reporter="test@example.com",
        )

        # Service should handle Redis failure gracefully
        request_id = service.submit_bug_report(bug_report)
        assert request_id is None

    def test_agent_failure_recovery(self, service_with_mocks):
        """Test recovery from agent failures"""
        service = service_with_mocks
        service.running = True

        # Setup agents with one failing agent
        service.agents = {"triage": Mock(), "failing_agent": Mock()}
        service.agents["failing_agent"].cleanup.side_effect = Exception("Agent failure")

        # Service should handle agent failure gracefully during shutdown
        service.stop_service()

        # Verify healthy agent was cleaned up
        service.agents["triage"].cleanup.assert_called_once()
        assert service.running == False
