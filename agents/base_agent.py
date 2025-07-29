import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage

from config import Config
from kafka_utils import KafkaProducerManager
from state_manager import StateManager

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.1,
            openai_api_key=Config.OPENAI_API_KEY,
        )
        self.kafka_producer = KafkaProducerManager()
        self.state_manager = StateManager()

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass

    @abstractmethod
    def process_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Process incoming message from Kafka"""
        pass

    def generate_request_id(self) -> str:
        """Generate a unique request ID"""
        return str(uuid.uuid4())

    def call_llm(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """Make a call to the LLM with proper error handling"""
        try:
            messages = []

            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            else:
                messages.append(SystemMessage(content=self.get_system_prompt()))

            messages.append(HumanMessage(content=user_message))

            response = self.llm(messages)
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error calling LLM in {self.agent_name}: {e}")
            raise

    def send_status_update(
        self,
        request_id: str,
        status: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Send status update to Kafka"""
        try:
            status_update = {
                "request_id": request_id,
                "status": status,
                "message": message,
                "agent": self.agent_name,
                "metadata": metadata or {},
            }

            self.kafka_producer.send_message(
                Config.STATUS_TOPIC, status_update, key=request_id
            )

        except Exception as e:
            logger.error(f"Error sending status update: {e}")

    def handle_error(
        self, request_id: str, error_message: str, exception: Exception = None
    ):
        """Handle errors and update state"""
        logger.error(
            f"Error in {self.agent_name} for request {request_id}: {error_message}"
        )

        if exception:
            logger.error(f"Exception details: {exception}")

        # Update state
        self.state_manager.set_error(request_id, f"{self.agent_name}: {error_message}")

        # Send status update
        self.send_status_update(request_id, "failed", error_message)

    def log_processing_start(self, request_id: str, step: str):
        """Log the start of processing"""
        logger.info(f"{self.agent_name} starting {step} for request {request_id}")
        self.send_status_update(request_id, "processing", f"Starting {step}")

    def log_processing_complete(self, request_id: str, step: str):
        """Log the completion of processing"""
        logger.info(f"{self.agent_name} completed {step} for request {request_id}")
        self.send_status_update(request_id, "completed", f"Completed {step}")

    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, "kafka_producer"):
            self.kafka_producer.close()
