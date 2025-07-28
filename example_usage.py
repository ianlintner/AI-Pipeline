#!/usr/bin/env python3

import time
import json
from datetime import datetime
from models import BugReport
from bug_report_service import BugReportTriageService

def create_sample_bug_reports():
    """Create sample bug reports for demonstration"""
    
    bug_reports = [
        BugReport(
            id="BUG-001",
            title="Login page crashes on mobile devices",
            description="The login page consistently crashes when accessed from mobile browsers, particularly on iOS Safari and Android Chrome.",
            reporter="john.doe@example.com",
            environment="Mobile browsers (iOS Safari 15.0, Android Chrome 96.0)",
            steps_to_reproduce="1. Open the application on a mobile device\n2. Navigate to /login\n3. Try to enter credentials\n4. App crashes immediately",
            expected_behavior="Login page should load normally and allow user authentication",
            actual_behavior="Page crashes with a JavaScript error and becomes unresponsive",
            attachments=["crash_log.txt", "screenshot.png"],
            metadata={"user_agent": "Mobile", "crash_count": 15, "affected_users": 230}
        ),
        
        BugReport(
            id="BUG-002", 
            title="Database connection timeout during peak hours",
            description="Users experience slow response times and timeout errors during peak usage hours (12-2 PM and 6-8 PM daily).",
            reporter="admin@example.com",
            environment="Production server - PostgreSQL 13.0, Node.js 16.0",
            steps_to_reproduce="1. Access the application during peak hours\n2. Perform any database operation\n3. Wait for response",
            expected_behavior="Database queries should complete within 2-3 seconds",
            actual_behavior="Queries timeout after 30 seconds, causing 500 errors",
            attachments=["server_logs.log", "database_metrics.csv"],
            metadata={"error_rate": "25%", "affected_endpoints": ["/api/users", "/api/orders"], "peak_load": "500 concurrent users"}
        ),
        
        BugReport(
            id="BUG-003",
            title="Typo in checkout button text",
            description="The checkout button displays 'Procced to Payment' instead of 'Proceed to Payment'.",
            reporter="qa.team@example.com", 
            environment="All browsers, production website",
            steps_to_reproduce="1. Add items to cart\n2. Go to checkout page\n3. Observe button text",
            expected_behavior="Button should display 'Proceed to Payment'",
            actual_behavior="Button displays 'Procced to Payment' with typo",
            attachments=["button_screenshot.png"],
            metadata={"page": "/checkout", "component": "payment_button"}
        )
    ]
    
    return bug_reports

def demo_service():
    """Demonstrate the bug report triage service"""
    
    print("=" * 60)
    print("Bug Report Triage Service Demonstration")
    print("=" * 60)
    
    # Create the service instance
    service = BugReportTriageService()
    
    try:
        # Note: This would normally start the service in background
        # For demo purposes, we'll show how it would work
        print("\n1. Initializing service components...")
        service.initialize_agents()
        service.initialize_consumers() 
        
        print("✓ Agents initialized:")
        for name, agent in service.agents.items():
            print(f"  - {agent.agent_name}")
        
        print("✓ Kafka consumers configured for topics:")
        for name, consumer in service.consumers.items():
            print(f"  - {name}: {consumer.topics}")
        
        # Create sample bug reports
        print("\n2. Creating sample bug reports...")
        bug_reports = create_sample_bug_reports()
        
        for i, bug_report in enumerate(bug_reports, 1):
            print(f"  Bug Report {i}: {bug_report.title}")
        
        # Simulate processing
        print("\n3. Processing workflow simulation...")
        print("   (In real usage, this would be done via Kafka messaging)")
        
        for bug_report in bug_reports:
            print(f"\n   Processing: {bug_report.title}")
            
            # Show triage analysis simulation
            print("   ├─ Triage Agent: Analyzing bug report...")
            print("   │  ├─ Priority assessment: Based on impact and urgency")  
            print("   │  ├─ Severity classification: Based on system impact")
            print("   │  └─ Category assignment: Based on affected component")
            
            # Show ticket creation simulation
            print("   ├─ Ticket Creation Agent: Formatting GitHub issue...")
            print("   │  ├─ Creating descriptive title")
            print("   │  ├─ Formatting issue body with markdown")
            print("   │  └─ Adding labels and assignees")
            
            # Show GitHub API simulation
            print("   ├─ GitHub API Agent: Creating issue...")
            print("   │  ├─ Preparing API payload")
            print("   │  ├─ Making API call (mocked)")
            print("   │  └─ Issue created successfully")
            
            # Show coordinator update
            print("   └─ Coordinator: Updating request status")
            
            time.sleep(1)  # Simulate processing time
        
        print("\n4. Service capabilities:")
        print("   ✓ LangChain integration for intelligent triage")
        print("   ✓ OpenAI GPT-4 for analysis and content generation")
        print("   ✓ Kafka messaging for agent communication")
        print("   ✓ Redis state management for request tracking")
        print("   ✓ GitHub API integration for issue creation")
        print("   ✓ Comprehensive error handling and monitoring")
        print("   ✓ Scalable agent-based architecture")
        
        print("\n5. Sample triage results:")
        
        # Show example triage output for first bug
        sample_triage = {
            "bug_id": "BUG-001",
            "priority": "high",
            "severity": "major", 
            "category": "frontend",
            "labels": ["bug", "mobile", "crash", "urgent"],
            "estimated_effort": "medium",
            "triage_notes": "Critical mobile compatibility issue affecting significant user base. Requires immediate attention from frontend team."
        }
        
        print(f"   Bug Report: {bug_reports[0].title}")
        print(f"   └─ {json.dumps(sample_triage, indent=6)}")
        
        print("\n6. GitHub issue example:")
        sample_github_issue = {
            "title": "🐛 Login page crashes on mobile devices",
            "labels": ["bug", "mobile", "crash", "urgent", "high-priority"],
            "body": """## Description
The login page consistently crashes when accessed from mobile browsers, particularly on iOS Safari and Android Chrome.

## Environment
Mobile browsers (iOS Safari 15.0, Android Chrome 96.0)

## Steps to Reproduce
1. Open the application on a mobile device
2. Navigate to /login
3. Try to enter credentials
4. App crashes immediately

## Expected Behavior
Login page should load normally and allow user authentication

## Actual Behavior
Page crashes with a JavaScript error and becomes unresponsive

## Additional Information  
- **Attachments:** crash_log.txt, screenshot.png
- **Affected Users:** 230
- **Crash Count:** 15

## Triage Information
- **Priority:** High
- **Severity:** Major  
- **Category:** Frontend
- **Estimated Effort:** Medium

Critical mobile compatibility issue affecting significant user base. Requires immediate attention from frontend team."""
        }
        
        print(f"   Title: {sample_github_issue['title']}")
        print(f"   Labels: {sample_github_issue['labels']}")
        print("   Body: [Well-formatted markdown issue description]")
        
    except Exception as e:
        print(f"Demo error: {e}")
    finally:
        # Cleanup
        service.stop_service()
    
    print("\n" + "=" * 60)
    print("Demo completed! Service is ready for production use.")
    print("=" * 60)

def show_usage_instructions():
    """Show how to use the service in production"""
    
    print("\n" + "=" * 60)
    print("PRODUCTION USAGE INSTRUCTIONS")
    print("=" * 60)
    
    print("""
1. SETUP REQUIREMENTS:
   - Kafka cluster running on localhost:9092 (or configure KAFKA_BOOTSTRAP_SERVERS)
   - Redis server running on localhost:6379 (or configure REDIS_URL)  
   - OpenAI API key (set OPENAI_API_KEY environment variable)
   - GitHub API token (set GITHUB_API_TOKEN environment variable)

2. ENVIRONMENT CONFIGURATION:
   Copy .env.example to .env and configure:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   GITHUB_API_TOKEN=your_github_token_here
   GITHUB_REPO_OWNER=your_github_username
   GITHUB_REPO_NAME=your_repo_name
   REDIS_URL=redis://localhost:6379
   ```

3. INSTALL DEPENDENCIES:
   ```bash
   pip install -r requirements.txt
   ```

4. START THE SERVICE:
   ```bash
   python bug_report_service.py
   ```

5. SUBMIT BUG REPORTS:
   ```python
   from bug_report_service import BugReportTriageService
   from models import BugReport
   
   service = BugReportTriageService()
   
   bug_report = BugReport(
       id="BUG-123",
       title="Application error on startup",
       description="App crashes when starting...",
       reporter="user@example.com"
   )
   
   request_id = service.submit_bug_report(bug_report)
   print(f"Request ID: {request_id}")
   ```

6. MONITOR PROGRESS:
   ```python
   # Check specific request
   status = service.get_request_status(request_id)
   print(status)
   
   # Check all active requests  
   active = service.get_all_active_requests()
   print(active)
   ```

7. ARCHITECTURE BENEFITS:
   - Scalable: Each agent can be scaled independently
   - Resilient: State management with Redis and error handling
   - Flexible: Easy to add new agents or modify workflow
   - Observable: Comprehensive logging and status tracking
   - Intelligent: LangChain + OpenAI for smart triage decisions
""")

if __name__ == "__main__":
    # Run the demonstration
    demo_service()
    
    # Show usage instructions
    show_usage_instructions()
