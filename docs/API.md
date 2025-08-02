# AI Pipeline API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Endpoints](#core-endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [OpenAPI Specification](#openapi-specification)

## Overview

The AI Pipeline provides a RESTful API for submitting bug reports and monitoring their processing status. The API follows REST principles and returns JSON responses.

**Base URL**: `http://localhost:8000/api/v1`

## Authentication

Currently, the API operates without authentication for development purposes. In production, implement:

- API Key authentication via `X-API-Key` header
- JWT tokens for user-based access
- Rate limiting per API key

## Core Endpoints

### Submit Bug Report

Submit a new bug report for processing.

```http
POST /api/v1/bug-reports
Content-Type: application/json

{
  "id": "BUG-001",
  "title": "Login page crashes on mobile devices",
  "description": "The login page consistently crashes when accessed from mobile browsers.",
  "reporter": "user@example.com",
  "environment": "Mobile browsers (iOS Safari, Android Chrome)",
  "steps_to_reproduce": "1. Open app on mobile\n2. Navigate to login\n3. App crashes",
  "expected_behavior": "Login should work normally",
  "actual_behavior": "Page crashes with JavaScript error",
  "attachments": ["screenshot.png", "error.log"],
  "metadata": {
    "user_agent": "Mozilla/5.0...",
    "session_id": "abc123"
  }
}
```

**Response (201 Created):**
```json
{
  "request_id": "req_abc123def456",
  "status": "submitted",
  "message": "Bug report submitted successfully",
  "estimated_processing_time": "2-5 minutes",
  "links": {
    "status": "/api/v1/requests/req_abc123def456/status",
    "self": "/api/v1/bug-reports/BUG-001"
  }
}
```

### Get Request Status

Monitor the processing status of a submitted bug report.

```http
GET /api/v1/requests/{request_id}/status
```

**Response (200 OK):**
```json
{
  "request_id": "req_abc123def456",
  "bug_report_id": "BUG-001",
  "status": "processing",
  "current_step": "triage",
  "progress": {
    "triage": {
      "status": "completed",
      "timestamp": "2024-01-15T10:30:00Z",
      "data": {
        "priority": "high",
        "severity": "major",
        "category": "frontend"
      }
    },
    "ticket_creation": {
      "status": "in_progress",
      "timestamp": "2024-01-15T10:32:00Z"
    }
  },
  "created_at": "2024-01-15T10:28:00Z",
  "updated_at": "2024-01-15T10:32:15Z",
  "processing_time_seconds": 255,
  "github_issue_number": null,
  "github_issue_url": null
}
```

### List Active Requests

Get all active processing requests.

```http
GET /api/v1/requests?status=active&limit=50&offset=0
```

**Response (200 OK):**
```json
{
  "requests": [
    {
      "request_id": "req_abc123def456",
      "bug_report_id": "BUG-001",
      "status": "processing",
      "current_step": "triage",
      "created_at": "2024-01-15T10:28:00Z",
      "processing_time_seconds": 120
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
}
```

### Health Check

Check the health status of the AI Pipeline service.

```http
GET /api/v1/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:35:00Z",
  "version": "1.0.0",
  "components": {
    "coordinator_agent": {
      "status": "healthy",
      "active_requests": 3
    },
    "triage_agent": {
      "status": "healthy",
      "processing_queue": 1
    },
    "ticket_creation_agent": {
      "status": "healthy",
      "processing_queue": 0
    },
    "github_api_agent": {
      "status": "healthy",
      "processing_queue": 2
    },
    "kafka": {
      "status": "healthy",
      "connected": true
    },
    "redis": {
      "status": "healthy",
      "connected": true
    },
    "openai": {
      "status": "healthy",
      "rate_limit_remaining": 4800
    }
  },
  "metrics": {
    "requests_processed_today": 147,
    "success_rate_24h": 98.5,
    "average_processing_time_seconds": 180
  }
}
```

### Get Processing Metrics

Retrieve system processing metrics.

```http
GET /api/v1/metrics?period=24h
```

**Response (200 OK):**
```json
{
  "period": "24h",
  "timestamp": "2024-01-15T10:35:00Z",
  "metrics": {
    "requests": {
      "total": 147,
      "successful": 145,
      "failed": 2,
      "success_rate": 98.64
    },
    "processing_times": {
      "average_seconds": 180,
      "median_seconds": 165,
      "p95_seconds": 300,
      "p99_seconds": 420
    },
    "agents": {
      "triage_agent": {
        "processed": 147,
        "success_rate": 100.0,
        "average_time_seconds": 45
      },
      "ticket_creation_agent": {
        "processed": 147,
        "success_rate": 99.32,
        "average_time_seconds": 60
      },
      "github_api_agent": {
        "processed": 146,
        "success_rate": 99.32,
        "average_time_seconds": 75
      }
    }
  }
}
```

## Data Models

### BugReport

```json
{
  "id": "string (required)",
  "title": "string (required)",
  "description": "string (required)",
  "reporter": "string (required)",
  "environment": "string (optional)",
  "steps_to_reproduce": "string (optional)",
  "expected_behavior": "string (optional)",
  "actual_behavior": "string (optional)",
  "attachments": ["string"] (optional),
  "created_at": "datetime (auto-generated)",
  "metadata": {
    "key": "value"
  } (optional)
}
```

### TriageResult

```json
{
  "bug_report_id": "string",
  "priority": "low|medium|high|critical",
  "severity": "minor|moderate|major|blocker",
  "category": "string",
  "labels": ["string"],
  "assignee_suggestion": "string (optional)",
  "duplicate_of": "string (optional)",
  "triage_notes": "string",
  "estimated_effort": "small|medium|large|extra-large (optional)",
  "created_at": "datetime"
}
```

### RequestState

```json
{
  "request_id": "string",
  "bug_report_id": "string",
  "status": "submitted|processing|completed|failed",
  "current_step": "string",
  "progress": {
    "step_name": {
      "status": "string",
      "timestamp": "datetime",
      "data": {}
    }
  },
  "error_message": "string (optional)",
  "github_issue_number": "integer (optional)",
  "github_issue_url": "string (optional)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "timestamp": "2024-01-15T10:35:00Z",
    "request_id": "req_abc123def456"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request data |
| `VALIDATION_ERROR` | 422 | Request data validation failed |
| `REQUEST_NOT_FOUND` | 404 | Request ID not found |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |

### Example Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "title": "Field is required",
      "reporter": "Invalid email format"
    },
    "timestamp": "2024-01-15T10:35:00Z",
    "request_id": null
  }
}
```

## Rate Limiting

### Rate Limit Headers

All responses include rate limiting headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642262400
X-RateLimit-Window: 3600
```

### Rate Limits

| Endpoint | Rate Limit | Window |
|----------|------------|---------|
| `POST /bug-reports` | 100 requests | 1 hour |
| `GET /requests/*` | 1000 requests | 1 hour |  
| `GET /health` | Unlimited | - |
| `GET /metrics` | 100 requests | 1 hour |

## OpenAPI Specification

### Complete OpenAPI 3.0 Specification

```yaml
openapi: 3.0.3
info:
  title: AI Pipeline API
  description: |
    Bug Report Triage Service API for automatically processing and creating GitHub issues from bug reports.
  version: 1.0.0
  contact:
    name: AI Pipeline Team
    email: support@ai-pipeline.example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://localhost:8000/api/v1
    description: Development server
  - url: https://api.ai-pipeline.example.com/v1
    description: Production server

paths:
  /bug-reports:
    post:
      summary: Submit bug report
      description: Submit a new bug report for processing
      operationId: submitBugReport
      tags:
        - Bug Reports
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BugReport'
            examples:
              mobile_crash:
                summary: Mobile app crash
                value:
                  id: "BUG-001"
                  title: "App crashes on iOS 15"
                  description: "The application crashes when opening on iOS 15 devices"
                  reporter: "user@example.com"
                  environment: "iOS 15.0, iPhone 12"
                  steps_to_reproduce: "1. Open app\n2. Navigate to main screen\n3. App crashes"
                  expected_behavior: "App should open normally"
                  actual_behavior: "App crashes with error code 1001"
      responses:
        '201':
          description: Bug report submitted successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SubmissionResponse'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /requests/{requestId}/status:
    get:
      summary: Get request status
      description: Get the current processing status of a bug report
      operationId: getRequestStatus
      tags:
        - Requests
      parameters:
        - name: requestId
          in: path
          required: true
          schema:
            type: string
          description: The request ID returned from bug report submission
      responses:
        '200':
          description: Request status retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RequestStatus'
        '404':
          description: Request not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /requests:
    get:
      summary: List requests
      description: Get a list of processing requests
      operationId: listRequests
      tags:
        - Requests
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [active, completed, failed, all]
            default: active
          description: Filter requests by status
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 50
          description: Maximum number of requests to return
        - name: offset
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
          description: Number of requests to skip
      responses:
        '200':
          description: Requests retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RequestList'

  /health:
    get:
      summary: Health check
      description: Get the health status of the service
      operationId: healthCheck
      tags:
        - System
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthStatus'
        '503':
          description: Service is unhealthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthStatus'

  /metrics:
    get:
      summary: Get metrics
      description: Get processing metrics for the specified period
      operationId: getMetrics
      tags:
        - System
      parameters:
        - name: period
          in: query
          schema:
            type: string
            enum: [1h, 24h, 7d, 30d]
            default: 24h
          description: Time period for metrics
      responses:
        '200':
          description: Metrics retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Metrics'

components:
  schemas:
    BugReport:
      type: object
      required:
        - id
        - title
        - description  
        - reporter
      properties:
        id:
          type: string
          description: Unique identifier for the bug report
          example: "BUG-001"
        title:
          type: string
          description: Title of the bug report
          example: "Login page crashes on mobile devices"
        description:
          type: string
          description: Detailed description of the bug
          example: "The login page consistently crashes when accessed from mobile browsers."
        reporter:
          type: string
          format: email
          description: Email of the person reporting the bug
          example: "user@example.com"
        environment:
          type: string
          description: Environment where bug occurred
          example: "Mobile browsers (iOS Safari, Android Chrome)"
        steps_to_reproduce:
          type: string
          description: Steps to reproduce the bug
          example: "1. Open app on mobile\n2. Navigate to login\n3. App crashes"
        expected_behavior:
          type: string
          description: Expected behavior
          example: "Login should work normally"
        actual_behavior:
          type: string
          description: Actual behavior observed
          example: "Page crashes with JavaScript error"
        attachments:
          type: array
          items:
            type: string
          description: List of attachment URLs
          example: ["screenshot.png", "error.log"]
        metadata:
          type: object
          additionalProperties: true
          description: Additional metadata
          example:
            user_agent: "Mozilla/5.0..."
            session_id: "abc123"

    SubmissionResponse:
      type: object
      properties:
        request_id:
          type: string
          example: "req_abc123def456"
        status:
          type: string
          example: "submitted"
        message:
          type: string
          example: "Bug report submitted successfully"
        estimated_processing_time:
          type: string
          example: "2-5 minutes"
        links:
          type: object
          properties:
            status:
              type: string
              example: "/api/v1/requests/req_abc123def456/status"
            self:
              type: string
              example: "/api/v1/bug-reports/BUG-001"

    RequestStatus:
      type: object
      properties:
        request_id:
          type: string
        bug_report_id:
          type: string
        status:
          type: string
          enum: [submitted, processing, completed, failed]
        current_step:
          type: string
        progress:
          type: object
          additionalProperties: true
        error_message:
          type: string
          nullable: true
        github_issue_number:
          type: integer
          nullable: true
        github_issue_url:
          type: string
          nullable: true
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
        processing_time_seconds:
          type: integer

    RequestList:
      type: object
      properties:
        requests:
          type: array
          items:
            $ref: '#/components/schemas/RequestStatus'
        pagination:
          type: object
          properties:
            total:
              type: integer
            limit:
              type: integer
            offset:
              type: integer
            has_more:
              type: boolean

    HealthStatus:
      type: object
      properties:
        status:
          type: string
          enum: [healthy, degraded, unhealthy]
        timestamp:
          type: string
          format: date-time
        version:
          type: string
        components:
          type: object
          additionalProperties: true
        metrics:
          type: object
          additionalProperties: true

    Metrics:
      type: object
      properties:
        period:
          type: string
        timestamp:
          type: string
          format: date-time
        metrics:
          type: object
          additionalProperties: true

    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: object
              additionalProperties: true
            timestamp:
              type: string
              format: date-time
            request_id:
              type: string
              nullable: true

  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - ApiKeyAuth: []
  - BearerAuth: []

tags:
  - name: Bug Reports
    description: Operations related to bug report submission
  - name: Requests
    description: Operations related to request status and monitoring
  - name: System
    description: System health and metrics operations
```

This API documentation provides comprehensive coverage of all endpoints, data models, error handling, and includes a complete OpenAPI specification for integration with API development tools.
