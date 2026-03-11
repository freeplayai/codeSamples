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
from freeplay import Freeplay, RecordPayload, CallInfo, SessionInfo


def _handle_tool_calls(
    tool_handlers: dict,
    tool_calls: list[tuple[str, str, dict]],
    provider: str,
    context: dict,
) -> list[dict]:
    """Execute tool handlers and return provider-formatted result messages."""
    results = []
    for call_id, name, args in tool_calls:
        handler = tool_handlers.get(name)
        if handler:
            output = handler(args, context)
        else:
            output = json.dumps({"error": f"Unknown tool: {name}"})
        results.append((call_id, output))

    if provider == "anthropic":
        return [
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": cid, "content": res}
                    for cid, res in results
                ],
            }
        ]

    return [
        {"role": "tool", "tool_call_id": cid, "content": res}
        for cid, res in results
    ]


def call_and_record(
    fp_client: Freeplay,
    project_id: str,
    template_name: str,
    environment: str,
    variables: dict,
    session_info: SessionInfo,
    tool_handlers: dict[str, Any] | None = None,
    history: list | None = None,
    parent_id: str | None = None,
) -> dict:
    """Fetch prompt from Freeplay, call the LLM, record, and loop on tool calls
    until the model returns a plain-text response."""
    tool_handlers = tool_handlers or {}
    history = list(history or [])
    context = {"parent_id": parent_id, "session_info": session_info}
    messages = None

    while True:
        formatted_prompt = fp_client.prompts.get_formatted(
            project_id=project_id,
            template_name=template_name,
            environment=environment,
            variables=variables,
            history=history,
        )

        provider = formatted_prompt.prompt_info.provider
        tool_schema = formatted_prompt.tool_schema

        # On the first iteration, seed the messages list from the formatted
        # prompt.  On subsequent iterations (tool-use loops) we keep building
        # on `messages` directly so the user message isn't re-injected by the
        # template — but we still call get_formatted above so Freeplay
        # recording and prompt metadata stay up to date.
        if messages is None:
            messages = list(formatted_prompt.llm_prompt)

        start = time.time()
        if provider == "anthropic":
            response_text, assistant_msg, tool_calls = _call_anthropic(
                formatted_prompt, tool_schema, messages,
            )
        elif provider == "openai":
            response_text, assistant_msg, tool_calls = _call_openai(
                formatted_prompt, tool_schema, messages,
            )
        else:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                "Expected 'anthropic' or 'openai'."
            )
        end = time.time()

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
                parent_id=parent_id,
            )
        )

        messages.append(assistant_msg)
        history.append(assistant_msg)

        if not tool_calls:
            break

        result_msgs = _handle_tool_calls(
            tool_handlers, tool_calls, provider, context,
        )
        messages.extend(result_msgs)
        history.extend(result_msgs)

    return {
        "llm_response": response_text,
        "all_messages": all_messages,
    }


def _call_anthropic(
    formatted_prompt,
    tool_schema,
    messages=None,
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
        messages=messages if messages is not None else formatted_prompt.llm_prompt,
        **call_kwargs,
    )

    assistant_msg = {"role": "assistant", "content": response.content}
    tool_calls = [
        (b.id, b.name, b.input) for b in response.content if isinstance(b, ToolUseBlock)
    ]
    response_text = "".join(
        b.text
        for b in response.content
        if getattr(b, "type", None) == "text" and b.text
    )
    return response_text, assistant_msg, tool_calls


def _call_openai(
    formatted_prompt,
    tool_schema,
    messages=None,
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
        messages=messages if messages is not None else formatted_prompt.llm_prompt,
        **call_kwargs,
    )

    message = response.choices[0].message
    tool_calls = [
        (tc.id, tc.function.name, json.loads(tc.function.arguments))
        for tc in (message.tool_calls or [])
    ]
    return message.content or "", message, tool_calls
