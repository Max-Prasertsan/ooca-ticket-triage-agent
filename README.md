# Support Ticket Triage Agent

An enterprise-grade AI agent system for automated customer support ticket triage, classification, and routing.

## Overview

This system leverages OpenAI's GPT models with integrated tooling to intelligently process incoming support tickets:

- **Urgency Classification**: Categorizes tickets as critical, high, medium, or low priority
- **Issue Type Detection**: Identifies billing, outage, bug, feature request, or account issues
- **Sentiment Analysis**: Gauges customer sentiment from very negative to very positive
- **Risk Detection**: Identifies churn risk, legal threats, and high-value accounts
- **Knowledge Base Search**: Retrieves relevant documentation and solutions
- **Customer Context**: Looks up customer history, tier, and account value
- **Intelligent Routing**: Routes to auto-respond, specialist, or human escalation
- **MCP Integration**: Connects to Slack, Jira, and PagerDuty for enterprise workflows

## Quick Start

```bash
# 1. Clone and setup
cd ooca-ticket-triage-agent
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure (optional - works without API key)
echo "OPENAI_API_KEY=sk-your-key-here" > .env
# Or Copy the example .env and add your key there.

# 3. Run interactive chat
python -m src.triage_agent.chat
```

## Project Structure

```
ooca-ticket-triage-agent/
├── .gitignore
├── README.md
├── pyproject.toml
├── requirements.txt
│
├── src/
│   ├── __init__.py
│   └── triage_agent/
│       ├── __init__.py
│       ├── config.py
│       ├── runner.py
│       ├── chat.py
│       ├── knowledge_base_data.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── ticket.py
│       │   ├── triage_output.py
│       │   └── tools.py
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── knowledge_base.py      # Native
│       │   ├── customer_history.py    # Native
│       │   ├── region_status.py       # Native
│       │   ├── slack.py               # MCP-style
│       │   ├── jira.py                # MCP-style
│       │   └── pagerduty.py           # MCP-style
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   └── triage_logic.py
│       │
│       └── prompts/
│           ├── __init__.py
│           └── system_prompt.py
│
└── tests/                              # <-- TEST DIRECTORY
    ├── __init__.py                     # Package marker
    ├── conftest.py                     # Shared fixtures (pytest auto-discovers)
    ├── test_agent.py                   # Agent initialization & processing
    ├── test_models.py                  # Pydantic model tests
    ├── test_tools_native.py            # KB, customer, region tools
    ├── test_tools_mcp.py               # Slack, Jira, PagerDuty tools
    ├── test_triage_logic.py            # Business rules & routing
    └── test_integration.py             # End-to-end flows
```

## Available Tools

The agent has 9 tools available for gathering context and taking actions:

### Native Tools
| Tool | Description |
|------|-------------|
| `knowledge_base_search` | Search internal KB for relevant articles and solutions |
| `customer_history` | Look up customer tier, lifetime value, past tickets, risk indicators |
| `region_status` | Check service health status by geographic region |

### MCP-Style Integration Tools
| Tool | Description |
|------|-------------|
| `slack_search` | Search Slack messages for internal context and discussions |
| `slack_post` | Post notifications to Slack channels for escalations |
| `jira_search` | Search Jira for related tickets and known issues |
| `jira_create` | Create Jira tickets for tracking and escalation |
| `pagerduty_incidents` | Check for active incidents that may explain issues |
| `pagerduty_create` | Page on-call engineers for critical issues |

## Usage

### Interactive Chat

```bash
python -m src.triage_agent.chat
```

| Command | Description |
|---------|-------------|
| `new` | Create ticket with full details |
| `quick` | Fast entry (subject + body + tier) |
| `sample` | Pick from sample tickets |
| `json` | Paste a JSON ticket |
| `help` | Show help |
| `quit` | Exit |

### Batch Processing

```bash
python -m src.triage_agent.runner                    # Process samples
python -m src.triage_agent.runner --input tickets.json
python -m src.triage_agent.runner --output results.json
python -m src.triage_agent.runner --quiet > results.json
```

### Programmatic Usage

```python
from src.triage_agent.core.agent import TriageAgent
from src.triage_agent.models.ticket import SupportTicket
from src.triage_agent.config import Config

# Initialize agent (includes all 9 tools by default)
agent = TriageAgent(Config())

# Create a ticket
ticket = SupportTicket(
    ticket_id="T-001",
    subject="Production database down",
    body="Our main database is not responding. All users affected.",
    customer_email="cto@enterprise.com",
    customer_tier="enterprise",
    customer_region="us-east"
)

# Process ticket
result = agent.triage(ticket)

# Access results
print(f"Urgency: {result.urgency.value}")           # critical
print(f"Action: {result.recommended_action.value}")  # escalate_to_human
print(f"Queue: {result.recommended_specialist_queue.value}")  # enterprise_success
print(f"Tools used: {len(result.tool_calls)}")      # 2+
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI (optional - falls back to rule-based without it)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.1

# Application
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=30

# Feature flags
ENABLE_KNOWLEDGE_BASE=true
ENABLE_CUSTOMER_HISTORY=true
ENABLE_REGION_STATUS=true
```

### Tool Configuration

```python
from src.triage_agent.tools import create_tool_registry

# All 9 tools (default)
registry = create_tool_registry(include_mcp=True)

# Native tools only (3 tools)
registry = create_tool_registry(include_mcp=False)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_agent.py -v
pytest tests/test_tools_mcp.py -v

# Run with coverage
pytest tests/ --cov=src/triage_agent --cov-report=html

# Run specific test class
pytest tests/test_tools_native.py::TestKnowledgeBaseTool -v
```

### Test Structure

| File | Tests |
|------|-------|
| `test_agent.py` | Agent initialization, ticket processing |
| `test_models.py` | Pydantic model validation, serialization |
| `test_tools_native.py` | KB search, customer history, region status |
| `test_tools_mcp.py` | Slack, Jira, PagerDuty tools |
| `test_triage_logic.py` | Urgency rules, risk detection, routing |
| `test_integration.py` | End-to-end triage flows |

## Extending the System

### Adding a New Tool

1. Create `src/triage_agent/tools/my_tool.py`:

```python
from pydantic import BaseModel, Field
from src.triage_agent.tools.base import BaseTool

class MyToolInput(BaseModel):
    query: str = Field(..., description="Search query")

class MyToolOutput(BaseModel):
    results: list[str] = Field(default_factory=list)

class MyTool(BaseTool[MyToolInput, MyToolOutput]):
    name = "my_tool"
    description = "Description for the LLM"
    input_model = MyToolInput
    output_model = MyToolOutput
    
    def _execute(self, input_data: MyToolInput) -> MyToolOutput:
        # Implementation
        return MyToolOutput(results=["result1", "result2"])
```

2. Register in `tools/__init__.py`
3. Add instructions to `prompts/system_prompt.py`

### Adding New Issue Types

Update `IssueType` enum in `models/triage_output.py`:

```python
class IssueType(str, Enum):
    BILLING = "billing"
    OUTAGE = "outage"
    # Add new type
    SECURITY = "security"
```

## Architecture Highlights

- **Clean Architecture**: Layered separation (models → tools → core → prompts)
- **Strategy Pattern**: Tools implement common `BaseTool` interface
- **Dependency Injection**: Tools injected via `ToolRegistry`
- **Graceful Degradation**: Falls back to rule-based triage without API key
- **Type Safety**: Full Pydantic validation at all boundaries
- **Hybrid AI + Rules**: LLM classification with deterministic business rule overrides


## License

MIT License - See LICENSE file for details.

---