import json
import logging
import threading
import time
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from models import BugReport, StatusUpdate, TicketStatus
from config import Config

logger = logging.getLogger(__name__)

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CoordinatorAgent")
        self.active_requests = {}
        self.timeout_monitor_thread = None
        self.monitoring = False
        
    def get_system_prompt(self) -> str:
        return """You are the coordinator agent responsible for managing the overall bug report processing workflow.

Your responsibilities include:
1. Receiving new bug reports and initiating the triage process
2. Monitoring the progress of active requests
3. Handling timeouts and retries
4. Providing status updates to external systems
5. Coordinating the workflow between different agents"""
    
    def start_monitoring(self):
        """Start the timeout monitoring thread"""
        if not self.monitoring:
            self.monitoring = True
            self.timeout_monitor_thread = threading.Thread(target=self._monitor_timeouts)
            self.timeout_monitor_thread.daemon = True
            self.timeout_monitor_thread.start()
            logger.info("Coordinator monitoring started")
    
    def stop_monitoring(self):
        """Stop the timeout monitoring thread"""
        self.monitoring = False
        if self.timeout_monitor_thread:
            self.timeout_monitor_thread.join(timeout=5)
        logger.info("Coordinator monitoring stopped")
    
    def submit_bug_report(self, bug_report: BugReport) -> str:
        """Submit a new bug report for processing"""
        try:
            request_id = self.generate_request_id()
            
            # Create initial status
            self.active_requests[request_id] = {
                "bug_report_id": bug_report.id,
                "status": "submitted",
                "created_at": time.time(),
                "last_updated": time.time()
            }
            
            # Send bug report to triage topic
            message = {
                "request_id": request_id,
                "bug_report": bug_report.model_dump()
            }
            
            success = self.kafka_producer.send_message(
                Config.BUG_REPORTS_TOPIC,
                message,
                key=request_id
            )
            
            if success:
                logger.info(f"Bug report {bug_report.id} submitted with request ID {request_id}")
                self.send_status_update(
                    request_id,
                    "submitted",
                    f"Bug report {bug_report.id} submitted for processing"
                )
                return request_id
            else:
                logger.error(f"Failed to submit bug report {bug_report.id}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting bug report: {e}")
            return None
    
    def process_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Process status updates and monitor progress"""
        if topic == Config.STATUS_TOPIC:
            self._process_status_update(message)
        else:
            logger.debug(f"Coordinator received message from topic {topic} - ignoring")
    
    def _process_status_update(self, message: Dict[str, Any]) -> None:
        """Process status updates from other agents"""
        try:
            request_id = message.get("request_id")
            status = message.get("status")
            agent = message.get("agent")
            
            if not request_id:
                return
            
            # Update active requests
            if request_id in self.active_requests:
                self.active_requests[request_id].update({
                    "status": status,
                    "last_updated": time.time(),
                    "last_agent": agent
                })
            
            # Log status update
            logger.info(f"Status update for {request_id}: {status} from {agent}")
            
            # Handle completion
            if status in ["completed", "failed"]:
                self._handle_request_completion(request_id, status, message)
                
        except Exception as e:
            logger.error(f"Error processing status update: {e}")
    
    def _handle_request_completion(self, request_id: str, final_status: str, message: Dict[str, Any]):
        """Handle completion of a request"""
        try:
            if request_id in self.active_requests:
                request_info = self.active_requests[request_id]
                processing_time = time.time() - request_info["created_at"]
                
                logger.info(f"Request {request_id} completed with status: {final_status}")
                logger.info(f"Processing time: {processing_time:.2f} seconds")
                
                # Log final status
                if final_status == "completed":
                    metadata = message.get("metadata", {})
                    github_url = metadata.get("github_issue_url")
                    issue_number = metadata.get("github_issue_number")
                    
                    logger.info(f"GitHub issue created: #{issue_number} - {github_url}")
                    
                    # Send final success notification
                    self.send_status_update(
                        request_id,
                        "completed",
                        f"Bug report processing completed successfully. GitHub issue #{issue_number} created.",
                        {
                            "processing_time_seconds": processing_time,
                            "github_issue_number": issue_number,
                            "github_issue_url": github_url
                        }
                    )
                else:
                    logger.error(f"Request {request_id} failed: {message.get('message', 'Unknown error')}")
                
                # Remove from active requests after a delay to allow final status propagation
                threading.Timer(30.0, lambda: self.active_requests.pop(request_id, None)).start()
                
        except Exception as e:
            logger.error(f"Error handling request completion: {e}")
    
    def _monitor_timeouts(self):
        """Monitor for timed out requests"""
        while self.monitoring:
            try:
                current_time = time.time()
                timeout_requests = []
                
                for request_id, request_info in self.active_requests.items():
                    if current_time - request_info["last_updated"] > Config.TIMEOUT_SECONDS:
                        timeout_requests.append(request_id)
                
                for request_id in timeout_requests:
                    self._handle_timeout(request_id)
                
                # Clean up old completed requests
                self._cleanup_old_requests(current_time)
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in timeout monitoring: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _handle_timeout(self, request_id: str):
        """Handle timed out requests"""
        try:
            request_info = self.active_requests.get(request_id)
            if not request_info:
                return
            
            logger.warning(f"Request {request_id} timed out (last status: {request_info.get('status', 'unknown')})")
            
            # Update state manager
            self.state_manager.set_error(
                request_id,
                f"Request timed out after {Config.TIMEOUT_SECONDS} seconds"
            )
            
            # Send timeout notification
            self.send_status_update(
                request_id,
                "failed",
                f"Request timed out after {Config.TIMEOUT_SECONDS} seconds",
                {
                    "timeout": True,
                    "last_status": request_info.get("status"),
                    "last_agent": request_info.get("last_agent")
                }
            )
            
            # Remove from active requests
            self.active_requests.pop(request_id, None)
            
        except Exception as e:
            logger.error(f"Error handling timeout for request {request_id}: {e}")
    
    def _cleanup_old_requests(self, current_time: float):
        """Clean up old completed requests from memory"""
        try:
            old_requests = []
            for request_id, request_info in self.active_requests.items():
                # Remove requests older than 1 hour
                if current_time - request_info["created_at"] > 3600:
                    old_requests.append(request_id)
            
            for request_id in old_requests:
                self.active_requests.pop(request_id, None)
                logger.debug(f"Cleaned up old request {request_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old requests: {e}")
    
    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get the current status of a request"""
        try:
            # Check in-memory cache first
            if request_id in self.active_requests:
                memory_status = self.active_requests[request_id]
                
                # Get detailed status from state manager
                state_status = self.state_manager.get_request_state(request_id)
                
                if state_status:
                    return {
                        "request_id": request_id,
                        "status": state_status.status,
                        "current_step": state_status.current_step,
                        "progress": state_status.progress,
                        "error_message": state_status.error_message,
                        "github_issue_number": state_status.github_issue_number,
                        "github_issue_url": state_status.github_issue_url,
                        "created_at": state_status.created_at.isoformat(),
                        "updated_at": state_status.updated_at.isoformat(),
                        "processing_time": time.time() - memory_status["created_at"]
                    }
            
            # Fall back to state manager only
            state_status = self.state_manager.get_request_state(request_id)
            if state_status:
                return {
                    "request_id": request_id,
                    "status": state_status.status,
                    "current_step": state_status.current_step,
                    "progress": state_status.progress,
                    "error_message": state_status.error_message,
                    "github_issue_number": state_status.github_issue_number,
                    "github_issue_url": state_status.github_issue_url,
                    "created_at": state_status.created_at.isoformat(),
                    "updated_at": state_status.updated_at.isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting request status: {e}")
            return None
    
    def get_all_active_requests(self) -> List[Dict[str, Any]]:
        """Get status of all active requests"""
        try:
            active_requests = []
            for request_id in self.active_requests.keys():
                status = self.get_request_status(request_id)
                if status:
                    active_requests.append(status)
            return active_requests
        except Exception as e:
            logger.error(f"Error getting active requests: {e}")
            return []
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        super().cleanup()
