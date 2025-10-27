"""
Gateway Agent for RPA Recovery Framework

The Gateway Agent is the central orchestrator that receives error notifications from
external RPA systems, standardizes them, and intelligently routes them to appropriate
recovery modules for resolution.
"""

from strands import Agent, tool
from strands.models.openai import OpenAIModel
from typing import Dict, Any
from datetime import datetime

from settings import FREE_PROVIDER_API_KEY, PROVIDER_API_BASE, PROVIDER_MODEL
from gateway.prompts import (
    GATEWAY_ORCHESTRATOR_PROMPT,
)
from gateway.models import RobotExceptionRequest

from modules.uierror.agent import ui_exception_handler
from agent_tools.database import available_modules


def robot_exception_handler(exception: RobotExceptionRequest) -> str:
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
                    "content": [{"type": "text", "text": GATEWAY_ORCHESTRATOR_PROMPT}],
                },
                {"role": "assistant", "content": [{"text": "okay"}]},
            ],
            tools=[
                available_modules,
                ui_exception_handler,  # Tool for handling UI exceptions
                route_to_human,  # Tool for routing to human operators
            ],
        )

        # Process the error through the agent
        response = agent(
            f"Process this error notification and route the error:\n\nError Data: {exception}"
        )

        return {
            "status": "accepted",
            "routing_response": response,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to process error notification: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }


@tool(
    name="route_to_human",
    description="Route the error to a human operator for manual intervention.",
)
def route_to_human(error_data: str) -> Dict[str, Any]:
    # TODO: When cockpit
    pass
