import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import redis

from config import Config
from models import RequestState, TicketStatus

logger = logging.getLogger(__name__)


class StateManager:
    def __init__(self):
        self.redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
        self.request_prefix = "request:"
        self.bug_report_prefix = "bug_report:"

    def _get_request_key(self, request_id: str) -> str:
        return f"{self.request_prefix}{request_id}"

    def _get_bug_report_key(self, bug_report_id: str) -> str:
        return f"{self.bug_report_prefix}{bug_report_id}"

    def create_request_state(
        self, request_id: str, bug_report_id: str, initial_step: str
    ) -> RequestState:
        """Create a new request state"""
        state = RequestState(
            request_id=request_id,
            bug_report_id=bug_report_id,
            status=TicketStatus.PENDING,
            current_step=initial_step,
        )

        try:
            key = self._get_request_key(request_id)
            self.redis_client.setex(
                key, Config.TIMEOUT_SECONDS, state.model_dump_json()
            )
            logger.info(f"Created request state for {request_id}")
            return state
        except Exception as e:
            logger.error(f"Error creating request state for {request_id}: {e}")
            raise

    def get_request_state(self, request_id: str) -> Optional[RequestState]:
        """Get request state by ID"""
        try:
            key = self._get_request_key(request_id)
            state_json = self.redis_client.get(key)

            if state_json:
                state_dict = json.loads(state_json)
                return RequestState(**state_dict)
            return None
        except Exception as e:
            logger.error(f"Error getting request state for {request_id}: {e}")
            return None

    def update_request_state(self, request_id: str, **updates) -> bool:
        """Update request state with new values"""
        try:
            state = self.get_request_state(request_id)
            if not state:
                logger.error(f"Request state not found for {request_id}")
                return False

            # Update fields
            for key, value in updates.items():
                if hasattr(state, key):
                    setattr(state, key, value)

            state.updated_at = datetime.now()

            # Save back to Redis
            key = self._get_request_key(request_id)
            self.redis_client.setex(
                key, Config.TIMEOUT_SECONDS, state.model_dump_json()
            )

            logger.info(f"Updated request state for {request_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating request state for {request_id}: {e}")
            return False

    def update_progress(self, request_id: str, step: str, data: Dict[str, Any]) -> bool:
        """Update progress information for a request"""
        try:
            state = self.get_request_state(request_id)
            if not state:
                return False

            state.progress[step] = {
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
            state.current_step = step
            state.updated_at = datetime.now()

            key = self._get_request_key(request_id)
            self.redis_client.setex(
                key, Config.TIMEOUT_SECONDS, state.model_dump_json()
            )

            return True
        except Exception as e:
            logger.error(f"Error updating progress for {request_id}: {e}")
            return False

    def set_error(self, request_id: str, error_message: str) -> bool:
        """Set error status for a request"""
        return self.update_request_state(
            request_id, status=TicketStatus.FAILED, error_message=error_message
        )

    def mark_completed(
        self, request_id: str, github_issue_number: int, github_issue_url: str
    ) -> bool:
        """Mark request as completed with GitHub issue details"""
        return self.update_request_state(
            request_id,
            status=TicketStatus.CREATED,
            github_issue_number=github_issue_number,
            github_issue_url=github_issue_url,
            current_step="completed",
        )

    def get_all_active_requests(self) -> Dict[str, RequestState]:
        """Get all active requests"""
        try:
            pattern = f"{self.request_prefix}*"
            keys = self.redis_client.keys(pattern)

            requests = {}
            for key in keys:
                state_json = self.redis_client.get(key)
                if state_json:
                    state_dict = json.loads(state_json)
                    state = RequestState(**state_dict)
                    request_id = key.replace(self.request_prefix, "")
                    requests[request_id] = state

            return requests
        except Exception as e:
            logger.error(f"Error getting active requests: {e}")
            return {}

    def cleanup_completed_requests(self, older_than_hours: int = 24) -> int:
        """Clean up completed requests older than specified hours"""
        try:
            requests = self.get_all_active_requests()
            cleaned = 0

            cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)

            for request_id, state in requests.items():
                if state.status in [TicketStatus.CREATED, TicketStatus.FAILED]:
                    if state.updated_at.timestamp() < cutoff_time:
                        key = self._get_request_key(request_id)
                        self.redis_client.delete(key)
                        cleaned += 1

            logger.info(f"Cleaned up {cleaned} completed requests")
            return cleaned

        except Exception as e:
            logger.error(f"Error cleaning up requests: {e}")
            return 0
