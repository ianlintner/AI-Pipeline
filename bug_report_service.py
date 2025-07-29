import logging
import threading
import signal
import sys
from typing import Dict, Any, List, Optional
from kafka_utils import KafkaConsumerManager
from agents import TriageAgent, TicketCreationAgent, GitHubAPIAgent, CoordinatorAgent
from models import BugReport
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bug_report_service.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class BugReportTriageService:
    def __init__(self):
        self.agents = {}
        self.consumers = {}
        self.coordinator = CoordinatorAgent()
        self.running = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def initialize_agents(self):
        """Initialize all agents"""
        logger.info("Initializing agents...")

        # Create agents
        self.agents = {
            "triage": TriageAgent(),
            "ticket_creation": TicketCreationAgent(),
            "github_api": GitHubAPIAgent(),
            "coordinator": self.coordinator,
        }

        logger.info("All agents initialized successfully")

    def initialize_consumers(self):
        """Initialize Kafka consumers for each agent"""
        logger.info("Initializing Kafka consumers...")

        # Triage Agent Consumer
        self.consumers["triage"] = KafkaConsumerManager(
            topics=[Config.BUG_REPORTS_TOPIC],
            group_id="triage-agent-group",
            message_handler=self.agents["triage"].process_message,
        )

        # Ticket Creation Agent Consumer
        self.consumers["ticket_creation"] = KafkaConsumerManager(
            topics=[Config.TRIAGE_TOPIC],
            group_id="ticket-creation-agent-group",
            message_handler=self.agents["ticket_creation"].process_message,
        )

        # GitHub API Agent Consumer
        self.consumers["github_api"] = KafkaConsumerManager(
            topics=[Config.TICKET_CREATION_TOPIC],
            group_id="github-api-agent-group",
            message_handler=self.agents["github_api"].process_message,
        )

        # Coordinator Consumer (for status updates)
        self.consumers["coordinator"] = KafkaConsumerManager(
            topics=[Config.STATUS_TOPIC],
            group_id="coordinator-agent-group",
            message_handler=self.coordinator.process_message,
        )

        logger.info("All Kafka consumers initialized successfully")

    def start_service(self):
        """Start the bug report triage service"""
        try:
            logger.info("Starting Bug Report Triage Service...")

            # Initialize components
            self.initialize_agents()
            self.initialize_consumers()

            # Start coordinator monitoring
            self.coordinator.start_monitoring()

            # Start consumers in separate threads
            consumer_threads = []
            for name, consumer in self.consumers.items():
                thread = threading.Thread(
                    target=consumer.start_consuming, name=f"{name}-consumer-thread"
                )
                thread.daemon = True
                thread.start()
                consumer_threads.append(thread)
                logger.info(f"Started {name} consumer thread")

            self.running = True
            logger.info("Bug Report Triage Service started successfully!")
            logger.info("Service is ready to process bug reports...")

            # Keep the main thread alive
            try:
                while self.running:
                    threading.Event().wait(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")

        except Exception as e:
            logger.error(f"Error starting service: {e}")
            self.stop_service()
            raise

    def stop_service(self):
        """Stop the bug report triage service"""
        logger.info("Stopping Bug Report Triage Service...")

        self.running = False

        # Stop consumers
        for name, consumer in self.consumers.items():
            try:
                consumer.stop_consuming()
                logger.info(f"Stopped {name} consumer")
            except Exception as e:
                logger.error(f"Error stopping {name} consumer: {e}")

        # Stop coordinator monitoring
        if self.coordinator:
            self.coordinator.stop_monitoring()

        # Cleanup agents
        for name, agent in self.agents.items():
            try:
                agent.cleanup()
                logger.info(f"Cleaned up {name} agent")
            except Exception as e:
                logger.error(f"Error cleaning up {name} agent: {e}")

        logger.info("Bug Report Triage Service stopped")

    def submit_bug_report(self, bug_report: BugReport) -> Optional[str]:
        """Submit a bug report for processing"""
        if not self.running:
            logger.error("Service is not running")
            return None

        try:
            request_id = self.coordinator.submit_bug_report(bug_report)
            if request_id:
                logger.info(
                    f"Bug report submitted successfully with request ID: {request_id}"
                )
            return request_id
        except Exception as e:
            logger.error(f"Error submitting bug report: {e}")
            return None

    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a bug report processing request"""
        try:
            return self.coordinator.get_request_status(request_id)
        except Exception as e:
            logger.error(f"Error getting request status: {e}")
            return None

    def get_all_active_requests(self) -> List[Dict[str, Any]]:
        """Get status of all active requests"""
        try:
            return self.coordinator.get_all_active_requests()
        except Exception as e:
            logger.error(f"Error getting active requests: {e}")
            return []

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.stop_service()
        sys.exit(0)

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the service"""
        try:
            health_status = {
                "service_running": self.running,
                "agents_count": len(self.agents),
                "consumers_count": len(self.consumers),
                "active_requests": (
                    len(self.coordinator.active_requests) if self.coordinator else 0
                ),
            }

            # Check individual components
            component_status = {}
            for name, agent in self.agents.items():
                try:
                    # Basic health check - agent should have required attributes
                    component_status[f"{name}_agent"] = {
                        "status": (
                            "healthy" if hasattr(agent, "agent_name") else "unhealthy"
                        ),
                        "agent_name": getattr(agent, "agent_name", "unknown"),
                    }
                except Exception as e:
                    component_status[f"{name}_agent"] = {
                        "status": "unhealthy",
                        "error": str(e),
                    }

            health_status["components"] = component_status
            health_status["overall_status"] = "healthy" if self.running else "unhealthy"

            return health_status

        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {"overall_status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    service = BugReportTriageService()
    try:
        service.start_service()
    except Exception as e:
        logger.error(f"Service failed to start: {e}")
        sys.exit(1)
