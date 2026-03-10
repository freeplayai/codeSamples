import json
import os
import sys
import time
from pathlib import Path

import anthropic
import openai
from anthropic import NotGiven
from dotenv import load_dotenv
from freeplay import CallInfo, Freeplay, RecordPayload, SessionInfo
from freeplay.resources.prompts import FormattedPrompt

load_dotenv(override=True)

"""
This sample project shows off one pattern for using Freeplay with LLMs.

This shows the basic workflow example of:
 1. Prepare all needed variables for the llm prompt
 2. Fetch the formatted prompt from Freeplay, pass in the variables, and get back a formatted prompt
 3. Make the LLM call using the formatted prompt and details
 4. Handle the response, parse out the raw output, message details, etc.
 5. Record the completion to Freeplay for observability

For this sample project, the mapping to Freeplay will look like:
 - session --> one session per report generation
   - completion --> response from LLM provider
"""

# --- Configuration ---
FREEPLAY_PROJECT_ID = os.environ.get("FREEPLAY_PROJECT_ID")
PROMPT_TEMPLATE_NAME = "CompensationPrepper"
ENVIRONMENT = "latest"
DATA_PATH = Path(__file__).parent / "data" / "sample_employees.jsonl"

###########################################
# Initialize the Freeplay client
###########################################
freeplay_client = Freeplay(
    freeplay_api_key=os.environ.get("FREEPLAY_API_KEY"),
    api_base=os.environ.get("FREEPLAY_API_BASE"),
)


def load_employees(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def find_employee(employees: list[dict], identifier: str) -> dict | None:
    """Find employee by ID, name (partial match), or 1-based index."""
    for emp in employees:
        if emp["employee_id"].lower() == identifier.lower():
            return emp
        if identifier.lower() in emp["name"].lower():
            return emp
    try:
        idx = int(identifier) - 1
        if 0 <= idx < len(employees):
            return employees[idx]
    except ValueError:
        pass
    return None


def build_prompt_variables(employee: dict) -> dict[str, str]:
    """Format employee data into the variables expected by the prompt template."""
    return {
        "job_info": json.dumps(employee["job_info"]),
        "comp_history": json.dumps(employee["comp_history"]),
        "one_off_payments": json.dumps(employee["one_off_payments"]),
        "perf_data": json.dumps(employee["perf_data"]),
        "locale": json.dumps(employee["locale"]),
    }


def call_and_record(
    freeplay_client: Freeplay,
    session: SessionInfo,
    employee: dict,
) -> str:
    """Call the LLM and record the completion to Freeplay."""

    ###########################################
    # Get the formatted prompt
    ###########################################
    formatted_prompt = freeplay_client.prompts.get_formatted(
        project_id=FREEPLAY_PROJECT_ID,
        template_name=PROMPT_TEMPLATE_NAME,
        environment=ENVIRONMENT,
        variables=build_prompt_variables(employee),
    )

    ###########################################
    # Call the LLM
    ###########################################

    provider = formatted_prompt.prompt_info.provider
    start_time = time.time()

    if provider == "anthropic":
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=formatted_prompt.prompt_info.model,
            system=formatted_prompt.system_content or NotGiven(),
            messages=formatted_prompt.llm_prompt,
            **formatted_prompt.prompt_info.model_parameters,
        )
        response_text = response.content[0].text
    elif provider == "openai":
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=formatted_prompt.prompt_info.model,
            messages=formatted_prompt.llm_prompt,
            **formatted_prompt.prompt_info.model_parameters,
        )
        response_text = response.choices[0].message.content
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Expected 'anthropic' or 'openai'."
        )

    end_time = time.time()

    ###########################################
    # Add the assistant message to the all messages
    ###########################################
    all_messages = formatted_prompt.all_messages(
        {"role": "assistant", "content": response_text}
    )

    ###########################################
    # Record the completion
    ###########################################
    freeplay_client.recordings.create(
        RecordPayload(
            # Project / Session
            project_id=FREEPLAY_PROJECT_ID,
            session_info=session,
            prompt_version_info=formatted_prompt.prompt_info,
            # LLM call info
            all_messages=all_messages,  # List of all messages in the session
            inputs=build_prompt_variables(
                employee
            ),  # Input variables used to generate the prompt
            call_info=CallInfo.from_prompt_info(
                formatted_prompt.prompt_info,
                start_time=start_time,
                end_time=end_time,
            ),
            # Custom client side eval results
            eval_results={"success": True},
        )
    )

    return response_text


def main():
    required = {"FREEPLAY_API_KEY", "FREEPLAY_API_BASE", "FREEPLAY_PROJECT_ID"}
    missing = [v for v in required if not os.environ.get(v)]
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        missing.append("ANTHROPIC_API_KEY or OPENAI_API_KEY")
    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    employees = load_employees(DATA_PATH)

    if len(sys.argv) < 2:
        print("Usage: python app.py <employee_id | name | number>\n")
        for i, emp in enumerate(employees):
            job, comp = emp["job_info"], emp["comp_history"][-1]
            print(
                f"  {i + 1}. {emp['name']} ({emp['employee_id']}) — "
                f"{job['title']} ({job['level']}) | "
                f"{comp['currency']} {comp['base_salary']:,} | {emp['locale']['city']}"
            )
        sys.exit(0)

    identifier = " ".join(sys.argv[1:])
    employee = find_employee(employees, identifier)
    if employee is None:
        print(f"Error: No employee matching '{identifier}'.")
        sys.exit(1)

    job, comp = employee["job_info"], employee["comp_history"][-1]
    print(f"Generating compensation report for {employee['name']}...")
    print(
        f"  {job['title']} ({job['level']}) | {comp['currency']} {comp['base_salary']:,} | {employee['locale']['city']}\n"
    )

    ###########################################
    # Create a new session
    ###########################################
    session = freeplay_client.sessions.create(
        custom_metadata={
            "employee_id": employee["employee_id"],
            "employee_name": employee["name"],
        }
    )

    print(call_and_record(freeplay_client, session, employee))


if __name__ == "__main__":
    main()
