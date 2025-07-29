import json
import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from config import Config
from models import BugReport, Priority, Severity, TicketStatus, TriageResult

logger = logging.getLogger(__name__)


class TriageAgent(BaseAgent):
    def __init__(self):
        super().__init__("TriageAgent")

    def get_system_prompt(self) -> str:
        return """You are a bug triage expert responsible for analyzing bug reports and determining their priority, severity, and categorization.

Your tasks:
1. Analyze the bug report description, steps to reproduce, and expected vs actual behavior
2. Determine the priority level (low, medium, high, critical)
3. Determine the severity level (minor, moderate, major, blocker)
4. Categorize the bug (e.g., frontend, backend, database, security, performance, ui/ux)
5. Suggest appropriate labels for the GitHub issue
6. Suggest an assignee if the bug clearly falls into a specific domain
7. Check if this might be a duplicate of existing issues
8. Estimate the effort required to fix (small, medium, large, extra-large)
9. Provide detailed triage notes explaining your reasoning

Priority Guidelines:
- CRITICAL: System down, data loss, security vulnerability
- HIGH: Major functionality broken, affects many users
- MEDIUM: Important feature not working correctly, affects some users
- LOW: Minor issues, cosmetic problems, edge cases

Severity Guidelines:
- BLOCKER: Prevents other work, system unusable
- MAJOR: Significant impact on functionality
- MODERATE: Noticeable impact but workarounds exist
- MINOR: Small impact, cosmetic issues

You must respond with a valid JSON object containing:
{
  "priority": "low|medium|high|critical",
  "severity": "minor|moderate|major|blocker",
  "category": "string describing the category",
  "labels": ["array", "of", "suggested", "labels"],
  "assignee_suggestion": "suggested assignee or null",
  "duplicate_of": "issue ID if duplicate or null",
  "triage_notes": "detailed explanation of your reasoning",
  "estimated_effort": "small|medium|large|extra-large"
}"""

    def process_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Process bug reports for triage"""
        if topic != Config.BUG_REPORTS_TOPIC:
            return

        try:
            # Parse the bug report
            bug_report_data = message.get("bug_report")
            request_id = message.get("request_id")

            if not bug_report_data or not request_id:
                logger.error("Invalid message format: missing bug_report or request_id")
                return

            bug_report = BugReport(**bug_report_data)

            # Update state
            self.state_manager.create_request_state(request_id, bug_report.id, "triage")

            self.log_processing_start(request_id, "bug triage")

            # Perform triage analysis
            triage_result = self._analyze_bug_report(bug_report, request_id)

            if triage_result:
                # Update state with triage results
                self.state_manager.update_progress(
                    request_id,
                    "triage_completed",
                    {
                        "priority": triage_result.priority,
                        "severity": triage_result.severity,
                        "category": triage_result.category,
                    },
                )

                # Send triage result to next topic
                triage_message = {
                    "request_id": request_id,
                    "bug_report": bug_report.model_dump(),
                    "triage_result": triage_result.model_dump(),
                }

                success = self.kafka_producer.send_message(
                    Config.TRIAGE_TOPIC, triage_message, key=request_id
                )

                if success:
                    self.log_processing_complete(request_id, "bug triage")
                    self.state_manager.update_request_state(
                        request_id, status=TicketStatus.TRIAGED
                    )
                else:
                    self.handle_error(
                        request_id, "Failed to send triage result to Kafka"
                    )
            else:
                self.handle_error(request_id, "Failed to analyze bug report")

        except Exception as e:
            if "request_id" in locals():
                self.handle_error(
                    request_id, f"Error processing bug report: {str(e)}", e
                )
            else:
                logger.error(f"Error processing message in TriageAgent: {e}")

    def _analyze_bug_report(
        self, bug_report: BugReport, request_id: str
    ) -> TriageResult:
        """Analyze bug report using LLM"""
        try:
            # Prepare the bug report information for analysis
            bug_info = f"""
Bug Report Analysis:

Title: {bug_report.title}
Description: {bug_report.description}
Reporter: {bug_report.reporter}
Environment: {bug_report.environment or 'Not specified'}

Steps to Reproduce:
{bug_report.steps_to_reproduce or 'Not provided'}

Expected Behavior:
{bug_report.expected_behavior or 'Not specified'}

Actual Behavior:
{bug_report.actual_behavior or 'Not specified'}

Additional Context:
- Created at: {bug_report.created_at}
- Attachments: {len(bug_report.attachments)} files
- Metadata: {json.dumps(bug_report.metadata, indent=2) if bug_report.metadata else 'None'}

Please analyze this bug report and provide your triage assessment in the required JSON format.
"""

            # Call LLM for analysis
            response = self.call_llm(bug_info)

            # Parse JSON response
            try:
                triage_data = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {response}")
                raise ValueError("Invalid JSON response from LLM")

            # Create TriageResult object
            triage_result = TriageResult(
                bug_report_id=bug_report.id,
                priority=Priority(triage_data["priority"]),
                severity=Severity(triage_data["severity"]),
                category=triage_data["category"],
                labels=triage_data.get("labels", []),
                assignee_suggestion=triage_data.get("assignee_suggestion"),
                duplicate_of=triage_data.get("duplicate_of"),
                triage_notes=triage_data["triage_notes"],
                estimated_effort=triage_data.get("estimated_effort"),
            )

            logger.info(
                f"Triage completed for bug {bug_report.id}: {triage_result.priority}/{triage_result.severity}"
            )
            return triage_result

        except Exception as e:
            logger.error(f"Error in bug report analysis: {e}")
            return None
