import json
import logging
from typing import Dict, Any
from agents.base_agent import BaseAgent
from models import BugReport, TriageResult, GitHubIssue, TicketCreationRequest, TicketStatus
from config import Config

logger = logging.getLogger(__name__)

class TicketCreationAgent(BaseAgent):
    def __init__(self):
        super().__init__("TicketCreationAgent")
    
    def get_system_prompt(self) -> str:
        return """You are a GitHub issue creation specialist responsible for converting triaged bug reports into well-formatted GitHub issues.

Your tasks:
1. Create a clear, descriptive title for the GitHub issue
2. Format the issue body with proper sections and markdown
3. Ensure all relevant information from the bug report is included
4. Use appropriate formatting for readability
5. Include reproduction steps, expected behavior, and actual behavior
6. Add any additional context that would help developers

The issue body should follow this structure:
## Description
[Clear description of the issue]

## Environment
[Environment details]

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Additional Information
[Any additional context, attachments, or notes]

## Triage Information
- **Priority:** [priority level]
- **Severity:** [severity level]
- **Category:** [category]
- **Estimated Effort:** [effort estimate]

[Triage notes]

You must respond with a valid JSON object containing:
{
  "title": "Clear, descriptive issue title",
  "body": "Formatted issue body with markdown",
  "labels": ["array", "of", "labels"],
  "assignees": ["array", "of", "assignees"],
  "milestone": "milestone name or null"
}"""
    
    def process_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Process triaged bug reports to create GitHub issues"""
        if topic != Config.TRIAGE_TOPIC:
            return
        
        try:
            # Parse the message
            request_id = message.get("request_id")
            bug_report_data = message.get("bug_report")
            triage_result_data = message.get("triage_result")
            
            if not all([request_id, bug_report_data, triage_result_data]):
                logger.error("Invalid message format: missing required fields")
                return
            
            bug_report = BugReport(**bug_report_data)
            triage_result = TriageResult(**triage_result_data)
            
            self.log_processing_start(request_id, "GitHub issue creation")
            
            # Create GitHub issue using LLM
            github_issue = self._create_github_issue(bug_report, triage_result, request_id)
            
            if github_issue:
                # Create ticket creation request
                ticket_request = TicketCreationRequest(
                    bug_report=bug_report,
                    triage_result=triage_result,
                    github_issue=github_issue,
                    request_id=request_id
                )
                
                # Update state
                self.state_manager.update_progress(
                    request_id,
                    "github_issue_created",
                    {
                        "title": github_issue.title,
                        "labels": github_issue.labels,
                        "assignees": github_issue.assignees
                    }
                )
                
                # Send to ticket creation topic
                ticket_message = {
                    "request_id": request_id,
                    "ticket_request": ticket_request.model_dump()
                }
                
                success = self.kafka_producer.send_message(
                    Config.TICKET_CREATION_TOPIC,
                    ticket_message,
                    key=request_id
                )
                
                if success:
                    self.log_processing_complete(request_id, "GitHub issue creation")
                    self.state_manager.update_request_state(
                        request_id,
                        status=TicketStatus.IN_PROGRESS,
                        current_step="creating_ticket"
                    )
                else:
                    self.handle_error(request_id, "Failed to send ticket creation request to Kafka")
            else:
                self.handle_error(request_id, "Failed to create GitHub issue")
                
        except Exception as e:
            if 'request_id' in locals():
                self.handle_error(request_id, f"Error creating GitHub issue: {str(e)}", e)
            else:
                logger.error(f"Error processing message in TicketCreationAgent: {e}")
    
    def _create_github_issue(self, bug_report: BugReport, triage_result: TriageResult, request_id: str) -> GitHubIssue:
        """Create GitHub issue using LLM"""
        try:
            # Prepare the information for GitHub issue creation
            issue_info = f"""
Create a GitHub issue for the following triaged bug report:

BUG REPORT:
Title: {bug_report.title}
Description: {bug_report.description}
Reporter: {bug_report.reporter}
Environment: {bug_report.environment or 'Not specified'}
Steps to Reproduce: {bug_report.steps_to_reproduce or 'Not provided'}
Expected Behavior: {bug_report.expected_behavior or 'Not specified'}
Actual Behavior: {bug_report.actual_behavior or 'Not specified'}
Attachments: {bug_report.attachments}
Created: {bug_report.created_at}

TRIAGE RESULTS:
Priority: {triage_result.priority}
Severity: {triage_result.severity}
Category: {triage_result.category}
Labels: {triage_result.labels}
Assignee Suggestion: {triage_result.assignee_suggestion or 'None'}
Estimated Effort: {triage_result.estimated_effort or 'Not specified'}
Triage Notes: {triage_result.triage_notes}

Please create a well-formatted GitHub issue with an appropriate title and body in the required JSON format.
"""

            # Call LLM for issue creation
            response = self.call_llm(issue_info)
            
            # Parse JSON response
            try:
                issue_data = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {response}")
                raise ValueError("Invalid JSON response from LLM")
            
            # Create GitHubIssue object
            github_issue = GitHubIssue(
                title=issue_data["title"],
                body=issue_data["body"],
                labels=issue_data.get("labels", []),
                assignees=issue_data.get("assignees", []),
                milestone=issue_data.get("milestone")
            )
            
            logger.info(f"GitHub issue created for bug {bug_report.id}: {github_issue.title}")
            return github_issue
            
        except Exception as e:
            logger.error(f"Error in GitHub issue creation: {e}")
            return None
