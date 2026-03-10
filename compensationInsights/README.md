# Compensation Insights

A sample application that generates AI-powered compensation reports for employees. Given an employee's job info, compensation history, performance data, and locale, it produces a structured compensation analysis using an LLM — with prompt management and observability powered by [Freeplay](https://freeplay.ai).

## How It Works

1. Load employee data from a JSONL file.
2. Fetch the current prompt template from Freeplay, injecting employee data as variables.
3. Call the configured LLM (Anthropic or OpenAI) with the formatted prompt.
4. Record the completion back to Freeplay for tracing and evaluation.

## Prerequisites

- Python 3.10+
- A [Freeplay](https://freeplay.ai) account with a project and a `CompensationPrepper` prompt template configured
- An API key for Anthropic and/or OpenAI (depending on the provider set in your Freeplay prompt)

## Setup

1. **Create a virtual environment:**

   ```bash
   python -m venv .compensationInsights
   source .compensationInsights/bin/activate
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
   | `FREEPLAY_API_BASE` | Freeplay API base URL |
   | `FREEPLAY_PROJECT_ID` | Your Freeplay project ID |
   | `ANTHROPIC_API_KEY` | Anthropic API key (if using Claude) |
   | `OPENAI_API_KEY` | OpenAI API key (if using GPT) |

## Usage

```bash
# List available employees
python app.py

# Generate a report by name, ID, or number
python app.py "Alice Johnson"
python app.py 1
```

## Project Structure

```
├── app.py              # Entry point — prompt formatting, LLM call, and Freeplay recording
├── data/
│   ├── sample_employees.csv    # Employee data (CSV format)
│   └── sample_employees.jsonl  # Employee data (JSONL format)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── .gitignore
```
