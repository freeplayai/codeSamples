"""HR Meeting Prep Agent — helps managers prepare for 1:1s and check-ins."""

import os

from dotenv import load_dotenv
from freeplay import Freeplay

from data import init_db, DB_PATH
from tools import TOOL_HANDLERS, make_report_tool
from llm import call_and_record

load_dotenv(override=True)

# ── Freeplay client ──────────────────────────────────────────────
fp_client = Freeplay(
    freeplay_api_key=os.environ["FREEPLAY_API_KEY"],
    api_base=f"{os.environ['FREEPLAY_API_URL']}/api",
)
PROJECT_ID = os.environ["FREEPLAY_PROJECT_ID"]
TEMPLATE_NAME = "HR-Manager"
ENVIRONMENT = "latest"


def run_agent():
    """Main chat loop."""
    if not os.path.exists(DB_PATH):
        init_db()

    session = fp_client.sessions.create()
    tool_handlers = {
        **TOOL_HANDLERS,
        "generate_report": make_report_tool(
            fp_client, PROJECT_ID, ENVIRONMENT, session.session_info,
        ),
    }

    print("=" * 60)
    print("  HR Meeting Prep Agent")
    print("  Helps you prepare for 1:1s with your direct reports.")
    print("  Type 'quit' or 'exit' to end the session.")
    print("=" * 60)
    print()

    history = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        history.append({"role": "user", "content": user_input})

        ###############################################
        # Create a Freepaly trace to wrap the Agent execution
        ###############################################
        trace_info = session.create_trace(input=user_input, agent_name="HR-Agent")

        ###############################################
        # Call the LLM and record the execution
        ###############################################
        result = call_and_record(
            fp_client=fp_client,
            project_id=PROJECT_ID,
            template_name=TEMPLATE_NAME,
            environment=ENVIRONMENT,
            variables={"user_input": user_input},
            session_info=session.session_info,
            tool_handlers=tool_handlers,
            history=history,
            parent_id=trace_info.trace_id,
        )

        ###############################################
        # Record the output of the Agent execution
        ###############################################
        trace_info.record_output(PROJECT_ID, result["llm_response"])

        print(f"\nAssistant: {result['llm_response']}\n")

        ###############################################
        # Update the history with the new messages
        ###############################################
        history = [msg for msg in result["all_messages"] if msg["role"] != "system"]


if __name__ == "__main__":
    run_agent()
