# Support Ticket Triage Agent

An enterprise-grade AI agent system for automated customer support ticket triage, classification, and routing.

## Overview

This system leverages OpenAI's GPT models to intelligently process incoming support tickets, performing:

- **Urgency Classification**: Categorizes tickets as critical, high, medium, or low priority
- **Information Extraction**: Identifies product, issue type, and customer sentiment
- **Knowledge Base Search**: Retrieves relevant documentation and solutions
- **Intelligent Routing**: Determines optimal next action (auto-respond, route to specialist, or escalate)
- **Risk Detection**: Identifies churn risk, dispute potential, and other customer risk signals

## Architecture Summary

```
ooca-ticket-triage-agent/
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
│   │   ├── classifier.py # Classification utilities
│   │   └── triage_logic.py  # Decision logic
│   ├── prompts/          # System prompts
│   │   └── system_prompt.py
│   ├── config.py         # Configuration management
│   ├── runner.py         # CLI entry point
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
cd ooca-ticket-triage-agent

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

Set your OpenAI API key as an environment variable:

```bash
# On macOS/Linux:
export OPENAI_API_KEY="your-api-key-here"

# On Windows (PowerShell):
$env:OPENAI_API_KEY="your-api-key-here"

# On Windows (CMD):
set OPENAI_API_KEY=your-api-key-here
```

Alternatively, create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-api-key-here
```

## Running the Agent

### Process Sample Tickets

```bash
# From project root
python -m src.triage_agent.runner

# Or with specific ticket file
python -m src.triage_agent.runner --input tickets.json

# Output to file
python -m src.triage_agent.runner --output results.json
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
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | Model to use | `gpt-4o` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `MAX_RETRIES` | API retry attempts | `3` |

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

---
