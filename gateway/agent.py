"""
Gateway Agent for RPA Recovery Framework

The Gateway Agent is the central orchestrator that receives error notifications from
external RPA systems, standardizes them, and intelligently routes them to appropriate
recovery modules for resolution.
"""

from typing import Any, Dict

from fastapi import WebSocket
from strands import Agent, ToolContext, tool
from strands.models.openai import OpenAIModel

from gateway.models import RobotExceptionRequest
from gateway.prompts import (
    GATEWAY_ORCHESTRATOR_PROMPT,
)

# from modules.uierror.agent import ui_exception_handler
from gateway.templates import ResponseToRPA
from settings import FREE_PROVIDER_API_KEY, PROVIDER_API_BASE, PROVIDER_MODEL


async def robot_exception_handler(
    exception: RobotExceptionRequest, websocket: WebSocket
) -> str:
    """
    Central Gateway Agent for the RPA Recovery Framework.

    Handles error intake, standardization, module routing, and session management.
    """
    model = OpenAIModel(
        client_args={
            "api_key": FREE_PROVIDER_API_KEY,
            "base_url": PROVIDER_API_BASE,
        },
        model_id=PROVIDER_MODEL,
    )

    try:
        agent = Agent(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": GATEWAY_ORCHESTRATOR_PROMPT}],
                },
                {"role": "assistant", "content": [{"text": "okay"}]},
            ],
            # tools=[available_modules, ui_exception_handler, route_to_human],
        )

        # Process the error through the agent
        response = await agent.invoke_async(
            f"Process this error notification and route the error:\n\nError Data: {exception}",
            invocation_state={"websocket": websocket},
        )

        response = await agent.invoke_async(
            "Given the conversation history, provide a structured response for the given model.",
            structured_output_model=ResponseToRPA,
        )

        return response.__str__()

    except Exception as _:
        return "Failed to process error notification."


@tool(
    name="route_to_human",
    description="Route the error to a human operator for manual intervention.",
    context=True,
)
async def route_to_human(error_data: str, tool_context: ToolContext) -> Dict[str, Any]:  # type: ignore
    # TODO: When cockpit
    pass
