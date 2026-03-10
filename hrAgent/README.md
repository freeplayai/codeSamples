# HR Meeting Prep Agent

A conversational AI agent that helps managers prepare for 1:1s and check-ins with their direct reports. Ask about an employee by name and get back performance reviews, goals, time-off balances, compensation details, and more — all pulled from a local HR database via tool calls.

## How It Works

The agent runs an interactive chat loop powered by [Freeplay](https://freeplay.ai) for prompt management, session tracking, and observability. On each turn it:

1. Fetches the current prompt template from Freeplay.
2. Calls the configured LLM (Anthropic or OpenAI).
3. Executes any tool calls the model requests against a local SQLite database.
4. Records every LLM call back to Freeplay for tracing and evaluation.

### Available Tools

| Tool | Description |
|---|---|
| `lookup_employee` | Find an employee by name (partial match) |
| `get_performance_reviews` | Review history with ratings and growth areas |
| `get_goals` | Current goals, statuses, and progress |
| `get_time_off` | PTO balance and upcoming scheduled time off |
| `get_compensation` | Salary band, current salary, and equity vesting |
| `list_direct_reports` | All direct reports for a given manager |

## Prerequisites

- Python 3.10+
- A [Freeplay](https://freeplay.ai) account with a project and prompt template configured
- An API key for Anthropic and/or OpenAI (depending on the provider set in your Freeplay prompt)

## Setup

1. **Clone the repo and create a virtual environment:**

   ```bash
   python -m venv .hrAgentEnv
   source .hrAgentEnv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**

   Copy the example env file and fill in your keys:

   ```bash
   cp .env.example .env
   ```

   | Variable | Description |
   |---|---|
   | `FREEPLAY_API_KEY` | Your Freeplay API key |
   | `FREEPLAY_API_URL` | Freeplay API base URL (default: `https://api.freeplay.ai`) |
   | `FREEPLAY_PROJECT_ID` | Your Freeplay project ID |
   | `ANTHROPIC_API_KEY` | Anthropic API key (if using Claude) |
   | `OPENAI_API_KEY` | OpenAI API key (if using GPT) |

4. **Seed the database (optional — happens automatically on first run):**

   ```bash
   python data.py
   ```

   This creates `hr.db` with a small set of mock employees, reviews, goals, compensation, and time-off data.

## Usage

```bash
python agent.py
```

Then chat naturally:

```
You: I have a 1:1 with Alice Johnson tomorrow. Can you pull together a prep summary?
Assistant: Here's a prep summary for your 1:1 with Alice Johnson ...
```

Type `quit` or `exit` to end the session.

## Project Structure

```
├── agent.py          # Entry point — chat loop and Freeplay session setup
├── llm.py            # LLM calling (Anthropic / OpenAI) with tool-use loop and Freeplay recording
├── tools.py          # Tool definitions (schemas) and implementations
├── data.py           # SQLite schema, seed data, and DB helpers
├── hr.db             # SQLite database (auto-generated)
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
└── .gitignore
```
