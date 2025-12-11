# Support Ticket Triage Agent

An enterprise-grade AI agent system for automated customer support ticket triage, classification, and routing.

## Overview

This system leverages OpenAI's GPT models to intelligently process incoming support tickets, performing:

- **Urgency Classification**: Categorizes tickets as critical, high, medium, or low priority
- **Information Extraction**: Identifies product, issue type, and customer sentiment
- **Knowledge Base Search**: Retrieves relevant documentation and solutions
- **Intelligent Routing**: Determines optimal next action (auto-respond, route to specialist, or escalate)
- **Risk Detection**: Identifies churn risk, dispute potential, and other customer risk signals

## Quick Start

```bash
# 1. Setup
cd ooca-ticket-triage-agent
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure (optional - works without API key using rule-based fallback)
echo "OPENAI_API_KEY=sk-your-key-here" > .env
# or use the example.env provided.

# 3. Run interactive chat
python -m src.triage_agent.chat
```

## Architecture Summary

```
ooca-ticket-triage-agent/
├── .env                  # Environment variables (create this)
├── src/triage_agent/
│   ├── models/           # Pydantic data models
│   │   ├── ticket.py     # Input ticket schema
│   │   ├── triage_output.py  # Agent output schema
│   │   └── tools.py      # Tool I/O schemas
│   ├── tools/            # Tool implementations
│   │   ├── base.py       # Abstract tool interface
│   │   ├── knowledge_base.py
│   │   ├── customer_history.py
│   │   └── region_status.py
│   ├── core/             # Agent logic
│   │   ├── agent.py      # Main agent orchestrator
│   │   └── triage_logic.py  # Decision logic
│   ├── prompts/          # System prompts
│   │   └── system_prompt.py
│   ├── config.py         # Configuration management
│   ├── runner.py         # Batch CLI runner
│   ├── chat.py           # Interactive terminal chat
│   └── knowledge_base_data.py  # Mock KB data
└── tests/
    └── test_sample_tickets.py
```

### Design Principles

- **Clean Architecture**: Clear separation between domain models, tools, and agent logic
- **Dependency Injection**: Tools are injected into the agent, enabling easy testing and extension
- **Single Responsibility**: Each module handles one concern
- **Open/Closed Principle**: Add new tools without modifying existing code
- **Type Safety**: Comprehensive Pydantic models with full type hints

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Virtual Environment Setup

```bash
# Clone or download the repository
cd support-triage-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the project root:

```bash
# Required for AI-powered triage (optional - falls back to rules without it)
OPENAI_API_KEY=sk-your-api-key-here

# Optional settings
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.1
LOG_LEVEL=INFO
MAX_RETRIES=3
```

Get your OpenAI API key at: https://platform.openai.com/api-keys

> **Note**: The agent works without an API key using rule-based fallback, but AI-powered triage provides better results.

## Usage

### Interactive Chat (Recommended)

The easiest way to interact with the agent:

```bash
python -m src.triage_agent.chat
```

**Available Commands:**

| Command | Description |
|---------|-------------|
| `new` | Create ticket with full details |
| `quick` | Fast entry (subject + body + tier) |
| `sample` | Pick from sample tickets |
| `json` | Paste a JSON ticket |
| `help` | Show help |
| `quit` | Exit |

**Example Session:**

```
> quick

⚡ Quick Ticket Entry

Subject: Cannot login to my account
Body: I've been locked out for 2 hours. Password reset emails not arriving.

Customer Tier [free/pro/enterprise]: enterprise

⏳ Processing ticket...

╭──────────────────────────────────────────────────╮
│                 📋 Triage Result                 │
├─────────────────────────┬────────────────────────┤
│ Urgency                 │ CRITICAL               │
│ Issue Type              │ account                │
│ Recommended Action      │ escalate_to_human      │
│ Specialist Queue        │ enterprise_success     │
╰─────────────────────────┴────────────────────────╯
```

### Batch Processing

Process multiple tickets from a file:

```bash
# Process sample tickets
python -m src.triage_agent.runner

# Process from JSON file
python -m src.triage_agent.runner --input tickets.json

# Output results to file
python -m src.triage_agent.runner --output results.json

# Quiet mode (JSON only)
python -m src.triage_agent.runner --quiet > results.json
```

### Programmatic Usage

```python
from src.triage_agent.core.agent import TriageAgent
from src.triage_agent.models.ticket import SupportTicket
from src.triage_agent.config import Config

# Initialize agent
config = Config()
agent = TriageAgent(config)

# Create a ticket
ticket = SupportTicket(
    ticket_id="T-001",
    subject="Cannot access my account",
    body="I've been locked out of my account for 2 days...",
    customer_email="customer@example.com",
    customer_tier="enterprise",
    timestamp="2024-01-15T10:30:00Z"
)

# Process ticket
result = agent.triage(ticket)

# Access results
print(f"Urgency: {result.urgency.value}")
print(f"Action: {result.recommended_action.value}")
print(f"Queue: {result.recommended_specialist_queue.value}")
print(f"Risk Signals: {[s.value for s in result.customer_risk_signals]}")

# Get full JSON
print(result.model_dump_json(indent=2))
```

## Example Output

```json
{
  "ticket_id": "T-001",
  "urgency": "high",
  "product": "authentication",
  "issue_type": "account",
  "customer_sentiment": "negative",
  "customer_risk_signals": ["churn_risk"],
  "recommended_action": "route_to_specialist",
  "recommended_specialist_queue": "tier_2",
  "knowledge_base_results": [
    {
      "id": "KB-AUTH-001",
      "title": "Account Recovery Steps",
      "url": "https://help.example.com/account-recovery",
      "relevance_score": 0.92
    }
  ],
  "suggested_reply": "I understand how frustrating it must be to be locked out...",
  "tool_calls": [
    {
      "tool_name": "knowledge_base_search",
      "inputs": {"query": "account locked out recovery"},
      "outputs": {"results": [...]}
    },
    {
      "tool_name": "customer_history",
      "inputs": {"customer_email": "customer@example.com"},
      "outputs": {"tier": "enterprise", "lifetime_value": 50000}
    }
  ]
}
```

## Extending the System

### Adding a New Tool

1. Create a new file in `src/triage_agent/tools/`:

```python
from src.triage_agent.tools.base import BaseTool
from src.triage_agent.models.tools import ToolInput, ToolOutput

class MyNewTool(BaseTool):
    name = "my_new_tool"
    description = "Description for the agent"
    
    def execute(self, input_data: ToolInput) -> ToolOutput:
        # Implementation
        pass
```

2. Register in `src/triage_agent/tools/__init__.py`
3. Add to agent's tool registry in config

### Adding New Issue Types

Update the `IssueType` enum in `src/triage_agent/models/triage_output.py`.

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/triage_agent

# Run specific test
pytest tests/test_sample_tickets.py -v
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | (empty - uses rule-based fallback) |
| `OPENAI_MODEL` | Model to use | `gpt-4o` |
| `OPENAI_TEMPERATURE` | Response temperature (0-2) | `0.1` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `MAX_RETRIES` | API retry attempts | `3` |
| `TIMEOUT_SECONDS` | Request timeout | `30` |

### Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_KNOWLEDGE_BASE` | Enable KB search tool | `true` |
| `ENABLE_CUSTOMER_HISTORY` | Enable customer lookup | `true` |
| `ENABLE_REGION_STATUS` | Enable region status | `true` |

## Security Notes

**Important:** Never commit your `.env` file! Add it to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

---