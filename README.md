# Bug Report Triage Service

A comprehensive Python service that uses LangChain, OpenAI, and Kafka to automatically read, triage, and create GitHub issues from bug reports. The service implements a multi-agent architecture where different agents handle specific aspects of the bug report processing workflow.

## 🏗️ Architecture

The service uses an **agent-based architecture** with **Kafka messaging** for communication between components:

```
Bug Report → Triage Agent → Ticket Creation Agent → GitHub API Agent → GitHub Issue
     ↓              ↓                  ↓                     ↓
Coordinator Agent ← Status Updates ← Status Updates ← Status Updates
```

### Agents

1. **Coordinator Agent**: Manages the overall workflow, handles timeouts, and provides status updates
2. **Triage Agent**: Analyzes bug reports using OpenAI to determine priority, severity, and categorization
3. **Ticket Creation Agent**: Creates well-formatted GitHub issues using OpenAI for content generation
4. **GitHub API Agent**: Handles actual GitHub API calls to create issues (includes mock implementation)

### Communication

- **Kafka Topics**: 
  - `bug-reports`: New bug reports for triage
  - `triage-results`: Triaged bug reports ready for ticket creation
  - `ticket-creation`: Formatted GitHub issues ready for API calls
  - `status-updates`: Status updates from all agents

- **State Management**: Redis for persistent request state tracking
- **LLM Integration**: OpenAI GPT-4 via LangChain for intelligent analysis

## 🚀 Features

- ✅ **Intelligent Triage**: Uses OpenAI to analyze priority, severity, and categorization
- ✅ **Multi-Agent Architecture**: Scalable, distributed processing
- ✅ **Kafka Messaging**: Reliable inter-agent communication
- ✅ **State Management**: Redis-based request tracking with timeouts
- ✅ **GitHub Integration**: Automatic issue creation (with mock support)
- ✅ **Comprehensive Logging**: Detailed logging and error handling
- ✅ **Status Monitoring**: Real-time progress tracking
- ✅ **Graceful Shutdown**: Proper cleanup and signal handling

## 📋 Requirements

### System Dependencies
- Python 3.8+
- Kafka cluster (default: localhost:9092)
- Redis server (default: localhost:6379)

### API Keys
- OpenAI API key
- GitHub API token (optional for production use)

## 🛠️ Installation

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bug-report-triage-service
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key (required)
   ```

3. **Start with Docker**
   ```bash
   # Make the script executable (Linux/Mac)
   chmod +x docker-start.sh
   
   # Start infrastructure only (Kafka, Redis, UIs)
   ./docker-start.sh infrastructure
   
   # OR start everything including the service
   ./docker-start.sh full
   
   # OR use interactive mode
   ./docker-start.sh
   ```

4. **Access web interfaces**
   - Kafka UI: http://localhost:8080
   - Redis Commander: http://localhost:8081

### Option 2: Manual Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bug-report-triage-service
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start external services**
   ```bash
   # Start Kafka (example with Docker)
   docker run -d --name kafka -p 9092:9092 \
     -e KAFKA_ZOOKEEPER_CONNECT=localhost:2181 \
     -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
     confluentinc/cp-kafka:latest
   
   # Start Redis (example with Docker)
   docker run -d --name redis -p 6379:6379 redis:alpine
   ```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# GitHub Configuration (for production)
GITHUB_API_TOKEN=your_github_token_here
GITHUB_REPO_OWNER=your_github_username
GITHUB_REPO_NAME=your_repo_name

# Redis Configuration
REDIS_URL=redis://localhost:6379
```

### Topics Configuration

The service automatically creates and uses these Kafka topics:
- `bug-reports`
- `triage-results` 
- `ticket-creation`
- `status-updates`

## 🏃‍♂️ Usage

### Starting the Service

```bash
python bug_report_service.py
```

### Submitting Bug Reports

```python
from bug_report_service import BugReportTriageService
from models import BugReport

# Create service instance
service = BugReportTriageService()

# Create a bug report
bug_report = BugReport(
    id="BUG-001",
    title="Login page crashes on mobile devices",
    description="The login page consistently crashes when accessed from mobile browsers.",
    reporter="user@example.com",
    environment="Mobile browsers (iOS Safari, Android Chrome)",
    steps_to_reproduce="1. Open app on mobile\n2. Navigate to login\n3. App crashes",
    expected_behavior="Login should work normally",
    actual_behavior="Page crashes with JavaScript error"
)

# Submit for processing
request_id = service.submit_bug_report(bug_report)
print(f"Request ID: {request_id}")
```

### Monitoring Progress

```python
# Check specific request status
status = service.get_request_status(request_id)
print(f"Status: {status['status']}")
print(f"Current Step: {status['current_step']}")

# Get all active requests
active_requests = service.get_all_active_requests()
for request in active_requests:
    print(f"Request {request['request_id']}: {request['status']}")
```

### Example Output

When a bug report is processed, you'll see output like:

```
2024-01-01 12:00:00 - TriageAgent - INFO - Starting bug triage for request abc-123
2024-01-01 12:00:05 - TriageAgent - INFO - Triage completed for bug BUG-001: high/major
2024-01-01 12:00:06 - TicketCreationAgent - INFO - Starting GitHub issue creation for request abc-123
2024-01-01 12:00:10 - GitHubAPIAgent - INFO - GitHub issue created successfully: #1234
2024-01-01 12:00:11 - CoordinatorAgent - INFO - Request abc-123 completed successfully
```

## 📊 Data Models

### BugReport
```python
{
    "id": "BUG-001",
    "title": "Login page crashes",
    "description": "Detailed description...",
    "reporter": "user@example.com",
    "environment": "iOS Safari 15.0",
    "steps_to_reproduce": "1. Step one\n2. Step two",
    "expected_behavior": "Should work normally",
    "actual_behavior": "Crashes with error",
    "attachments": ["file1.log", "screenshot.png"],
    "created_at": "2024-01-01T12:00:00Z",
    "metadata": {"key": "value"}
}
```

### TriageResult
```python
{
    "bug_report_id": "BUG-001",
    "priority": "high",           # low, medium, high, critical
    "severity": "major",          # minor, moderate, major, blocker  
    "category": "frontend",
    "labels": ["bug", "mobile", "crash"],
    "assignee_suggestion": "frontend-team",
    "estimated_effort": "medium", # small, medium, large, extra-large
    "triage_notes": "Critical mobile issue..."
}
```

## 🧪 Testing

### Run the Demo

```bash
python example_usage.py
```

This will:
1. Initialize all service components
2. Show sample bug reports
3. Simulate the complete workflow
4. Display example triage results and GitHub issues

### Manual Testing

1. Start the service: `python bug_report_service.py`
2. In another terminal, submit test bug reports using the example code
3. Monitor the logs to see the workflow progression
4. Check Redis for state persistence
5. Verify Kafka topics receive messages

## 🔧 Development

### Adding New Agents

1. Create a new agent class inheriting from `BaseAgent`:

```python
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("CustomAgent")
    
    def get_system_prompt(self) -> str:
        return "Your agent's system prompt..."
    
    def process_message(self, topic: str, message: Dict[str, Any]) -> None:
        # Process incoming messages
        pass
```

2. Add the agent to `bug_report_service.py`
3. Configure Kafka consumer for the agent
4. Update the workflow as needed

### Extending Functionality

- **Add new triage criteria**: Modify the `TriageAgent` system prompt
- **Custom GitHub issue format**: Update `TicketCreationAgent` prompt  
- **Additional integrations**: Create new agents for Slack, email, etc.
- **Enhanced monitoring**: Add metrics collection and dashboards

## 🚨 Error Handling

The service includes comprehensive error handling:

- **Agent failures**: Errors are logged and status is updated
- **Kafka connectivity**: Automatic retries and graceful degradation
- **LLM failures**: Retry logic with exponential backoff
- **Timeouts**: Configurable timeouts with automatic cleanup
- **State corruption**: Redis fallback and recovery mechanisms

## 📈 Scalability

The architecture supports horizontal scaling:

- **Agent scaling**: Run multiple instances of each agent type
- **Kafka partitioning**: Distribute load across partitions
- **Redis clustering**: Scale state management
- **Load balancing**: Use Kafka consumer groups for distribution

## 🔒 Security Considerations

- Store API keys securely (environment variables, secrets management)
- Use GitHub fine-grained tokens with minimal required permissions
- Implement input validation for bug reports
- Consider message encryption for sensitive data
- Regular security updates for dependencies

## 📝 Logging

Logs are written to:
- **Console**: Real-time monitoring during development
- **File**: `bug_report_service.log` for persistent storage
- **Structured format**: Timestamp, logger name, level, message

Log levels:
- `INFO`: Normal operations, status updates
- `WARNING`: Recoverable issues, timeouts
- `ERROR`: Failures, exceptions
- `DEBUG`: Detailed tracing (disabled by default)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain**: For LLM integration framework
- **OpenAI**: For GPT-4 API
- **Apache Kafka**: For reliable messaging
- **Redis**: For state management
- **GitHub**: For issue tracking integration

---

## Quick Start Commands

```bash
# 1. Setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys

# 2. Start dependencies (Docker)
docker run -d -p 9092:9092 --name kafka confluentinc/cp-kafka:latest
docker run -d -p 6379:6379 --name redis redis:alpine

# 3. Run demo
python example_usage.py

# 4. Start service
python bug_report_service.py
```

**The service is now ready to intelligently triage your bug reports! 🎉**
