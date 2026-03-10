"""LLM calling and Freeplay recording utilities.

Supports Anthropic and OpenAI providers with agentic tool-use loops.
Provider selection is driven by the Freeplay prompt configuration.
"""

import json
import time
from typing import Any

import anthropic
from anthropic import NotGiven
from anthropic.types import ToolUseBlock
import openai
from freeplay import Freeplay, RecordPayload, CallInfo, SessionInfo, TraceInfo


def call_and_record(
    fp_client: Freeplay,
    project_id: str,
    template_name: str,
    environment: str,
    variables: dict,
    session_info: SessionInfo,
    tool_handlers: dict[str, Any] | None = None,
    tool_definitions: list | None = None,
    history: list | None = None,
    trace_info: TraceInfo | None = None,
) -> dict:
    """Fetch prompt from Freeplay, call the LLM, and record each call.

    Each LLM invocation is recorded individually to Freeplay.
    For tool-call turns the recorded response is the tool call itself.
    The loop continues until the LLM returns a plain text response.
    """
    tool_handlers = tool_handlers or {}
    history = list(history or [])

    while True:
        # 1. Fetch & format prompt with the latest history
        formatted_prompt = fp_client.prompts.get_formatted(
            project_id=project_id,
            template_name=template_name,
            environment=environment,
            variables=variables,
            history=history,
        )

        provider = formatted_prompt.prompt_info.provider
        tool_schema = formatted_prompt.tool_schema or tool_definitions
        tool_schema = _format_tools_for_provider(tool_schema, provider) if tool_schema else None

        # 2. Call the LLM
        start = time.time()
        if provider == "anthropic":
            response_text, assistant_msg, tool_calls = _call_anthropic(
                formatted_prompt, tool_schema,
            )
        elif provider == "openai":
            response_text, assistant_msg, tool_calls = _call_openai(
                formatted_prompt, tool_schema,
            )
        else:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                "Expected 'anthropic' or 'openai'."
            )
        end = time.time()

        # 3. Record THIS call to Freeplay
        all_messages = formatted_prompt.all_messages(assistant_msg)
        fp_client.recordings.create(
            RecordPayload(
                project_id=project_id,
                all_messages=all_messages,
                session_info=session_info,
                inputs=variables,
                prompt_version_info=formatted_prompt.prompt_info,
                call_info=CallInfo.from_prompt_info(
                    formatted_prompt.prompt_info, start, end
                ),
                tool_schema=tool_schema,
                trace_info=trace_info,
            )
        )

        # 4. Add assistant message to history
        history.append(assistant_msg)

        # 5. If no tool calls, we're done
        if not tool_calls:
            break

        # 6. Execute tools and add results to history
        results = [
            (cid, _execute_tool(tool_handlers, name, args))
            for cid, name, args in tool_calls
        ]

        if provider == "anthropic":
            history.append({
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": cid, "content": res}
                    for cid, res in results
                ],
            })
        elif provider == "openai":
            for cid, res in results:
                history.append({
                    "role": "tool",
                    "tool_call_id": cid,
                    "content": res,
                })

    return {
        "llm_response": response_text,
        "all_messages": all_messages,
    }


def _format_tools_for_provider(tools: list, provider: str) -> list:
    """Convert normalized tool definitions (name, description, parameters)
    to the format expected by each provider.

    Mirrors the conversion logic in Freeplay's BoundPrompt.__format_tool_schema.
    If tools are already in a provider-specific format they pass through unchanged.
    """
    if not tools:
        return tools
    sample = tools[0]

    # Already provider-formatted (e.g. from formatted_prompt.tool_schema)
    if provider == "openai" and sample.get("type") == "function":
        return tools
    if provider == "anthropic" and "input_schema" in sample:
        return tools

    # Normalized format → provider-specific
    if provider == "openai":
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t["parameters"],
                },
            }
            for t in tools
        ]
    if provider == "anthropic":
        return [
            {
                "name": t["name"],
                "description": t.get("description", ""),
                "input_schema": t["parameters"],
            }
            for t in tools
        ]
    return tools


def _execute_tool(tool_handlers: dict, name: str, args: dict) -> str:
    handler = tool_handlers.get(name)
    if handler:
        return handler(args)
    return json.dumps({"error": f"Unknown tool: {name}"})


# ── Anthropic ────────────────────────────────────────────────────────


def _call_anthropic(
    formatted_prompt, tool_schema,
) -> tuple[str, dict, list[tuple[str, str, dict]]]:
    """Single Anthropic API call. Returns (text, assistant_msg, tool_calls)."""
    client = anthropic.Anthropic()

    call_kwargs: dict[str, Any] = dict(
        system=formatted_prompt.system_content or NotGiven(),
        model=formatted_prompt.prompt_info.model,
        **formatted_prompt.prompt_info.model_parameters,
    )
    if tool_schema:
        call_kwargs["tools"] = tool_schema

    response = client.messages.create(
        messages=formatted_prompt.llm_prompt, **call_kwargs,
    )

    assistant_msg = {"role": "assistant", "content": response.content}
    tool_calls = [
        (b.id, b.name, b.input)
        for b in response.content if isinstance(b, ToolUseBlock)
    ]
    response_text = "".join(
        b.text for b in response.content
        if getattr(b, "type", None) == "text" and b.text
    )
    return response_text, assistant_msg, tool_calls


# ── OpenAI ───────────────────────────────────────────────────────────


def _call_openai(
    formatted_prompt, tool_schema,
) -> tuple[str, Any, list[tuple[str, str, dict]]]:
    """Single OpenAI API call. Returns (text, assistant_msg, tool_calls)."""
    client = openai.OpenAI()

    call_kwargs: dict[str, Any] = dict(
        model=formatted_prompt.prompt_info.model,
        **formatted_prompt.prompt_info.model_parameters,
    )
    if tool_schema:
        call_kwargs["tools"] = tool_schema

    response = client.chat.completions.create(
        messages=formatted_prompt.llm_prompt, **call_kwargs,
    )

    message = response.choices[0].message
    tool_calls = [
        (tc.id, tc.function.name, json.loads(tc.function.arguments))
        for tc in (message.tool_calls or [])
    ]
    return message.content or "", message, tool_calls
