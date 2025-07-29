import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
    GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
    GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Kafka Topics
    BUG_REPORTS_TOPIC = "bug-reports"
    TRIAGE_TOPIC = "triage-results"
    TICKET_CREATION_TOPIC = "ticket-creation"
    STATUS_TOPIC = "status-updates"

    # Agent settings
    OPENAI_MODEL = "gpt-4"
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 300
