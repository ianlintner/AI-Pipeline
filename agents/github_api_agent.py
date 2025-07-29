import json
import logging
import requests
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from models import TicketCreationRequest, TicketStatus
from config import Config

logger = logging.getLogger(__name__)


class GitHubAPIAgent(BaseAgent):
    def __init__(self):
        super().__init__("GitHubAPIAgent")
        self.github_headers = {
            "Authorization": f"token {Config.GITHUB_API_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }
        self.base_url = f"https://api.github.com/repos/{Config.GITHUB_REPO_OWNER}/{Config.GITHUB_REPO_NAME}"

    def get_system_prompt(self) -> str:
        return """You are a GitHub API integration agent responsible for creating issues in GitHub repositories.
        
Your primary task is to take formatted GitHub issue data and create actual issues using the GitHub API.
You handle API errors gracefully and provide meaningful feedback about the issue creation process."""

    def process_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Process ticket creation requests"""
        if topic != Config.TICKET_CREATION_TOPIC:
            return

        try:
            # Parse the message
            request_id = message.get("request_id")
            ticket_request_data = message.get("ticket_request")

            if not request_id or not ticket_request_data:
                logger.error(
                    "Invalid message format: missing request_id or ticket_request"
                )
                return

            ticket_request = TicketCreationRequest(**ticket_request_data)

            self.log_processing_start(request_id, "GitHub issue creation via API")

            # Create the GitHub issue
            issue_response = self._create_github_issue_via_api(
                ticket_request, request_id
            )

            if issue_response:
                # Update state with success
                self.state_manager.mark_completed(
                    request_id, issue_response["number"], issue_response["html_url"]
                )

                self.log_processing_complete(
                    request_id, "GitHub issue creation via API"
                )

                # Send final status update
                self.send_status_update(
                    request_id,
                    "completed",
                    f"GitHub issue #{issue_response['number']} created successfully",
                    {
                        "github_issue_number": issue_response["number"],
                        "github_issue_url": issue_response["html_url"],
                        "title": issue_response["title"],
                    },
                )
            else:
                self.handle_error(request_id, "Failed to create GitHub issue via API")

        except Exception as e:
            if "request_id" in locals():
                self.handle_error(request_id, f"Error in GitHub API agent: {str(e)}", e)
            else:
                logger.error(f"Error processing message in GitHubAPIAgent: {e}")

    def _create_github_issue_via_api(
        self, ticket_request: TicketCreationRequest, request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Create GitHub issue using the GitHub API (or mock API)"""
        try:
            github_issue = ticket_request.github_issue

            # Prepare the issue payload
            issue_payload = {
                "title": github_issue.title,
                "body": github_issue.body,
                "labels": github_issue.labels,
                "assignees": github_issue.assignees,
            }

            if github_issue.milestone:
                issue_payload["milestone"] = github_issue.milestone

            # For demonstration purposes, we'll use a mock API response
            # In a real implementation, you would make an actual API call:
            # response = requests.post(f"{self.base_url}/issues",
            #                         json=issue_payload,
            #                         headers=self.github_headers)

            # Mock GitHub API response for demonstration
            mock_response = self._mock_github_api_call(issue_payload, request_id)

            if mock_response:
                logger.info(
                    f"GitHub issue created successfully: #{mock_response['number']}"
                )
                return mock_response
            else:
                logger.error("Failed to create GitHub issue")
                return None

        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            return None

    def _mock_github_api_call(
        self, issue_payload: Dict[str, Any], request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Mock GitHub API call for demonstration purposes"""
        try:
            # Simulate API call delay
            import time

            time.sleep(1)

            # Mock successful response
            import random

            issue_number = random.randint(1000, 9999)

            mock_response = {
                "id": random.randint(100000, 999999),
                "number": issue_number,
                "title": issue_payload["title"],
                "body": issue_payload["body"],
                "labels": [
                    {"name": label} for label in issue_payload.get("labels", [])
                ],
                "assignees": [
                    {"login": assignee}
                    for assignee in issue_payload.get("assignees", [])
                ],
                "state": "open",
                "html_url": f"https://github.com/{Config.GITHUB_REPO_OWNER}/{Config.GITHUB_REPO_NAME}/issues/{issue_number}",
                "url": f"https://api.github.com/repos/{Config.GITHUB_REPO_OWNER}/{Config.GITHUB_REPO_NAME}/issues/{issue_number}",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }

            # Log the mock API call
            logger.info(f"MOCK GitHub API Call for request {request_id}:")
            logger.info(f"  URL: POST {self.base_url}/issues")
            logger.info(f"  Payload: {json.dumps(issue_payload, indent=2)}")
            logger.info(f"  Response: Issue #{issue_number} created")
            logger.info(f"  URL: {mock_response['html_url']}")

            return mock_response

        except Exception as e:
            logger.error(f"Error in mock GitHub API call: {e}")
            return None

    def _make_real_github_api_call(
        self, issue_payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make actual GitHub API call (commented out for safety)"""
        """
        Uncomment and modify this method to make real GitHub API calls:
        
        try:
            response = requests.post(
                f"{self.base_url}/issues",
                json=issue_payload,
                headers=self.github_headers,
                timeout=30
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
        """
        pass
