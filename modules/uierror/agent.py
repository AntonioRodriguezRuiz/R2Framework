from strands import Agent, tool
from strands.models.openai import OpenAIModel
from settings import (
    PROVIDER_API_BASE,
    PROVIDER_API_KEY,
    PROVIDER_VISION_MODEL,
    OLLAMA_URL,
)
from modules.uierror.prompts import (
    RECOVERY_PLANNER_PROMPT,
    RECOVERY_STEP_EXECUTION_PROMPT,
    COMPUTER_USE_DOUBAO,
)
from modules.uierror.uitars import (
    parse_action_to_structure_output,
    parsing_response_to_pyautogui_code,
)
from agent_tools.image import take_screenshot
import pyautogui  # noqa
import httpx  # For Ollama usage


@tool(
    description="Generate a recovery plan for a UI error based on the provided task and action history.",
)
def ui_exception_handler(task: str, action_history: str) -> str:
    """
    Generate a recovery plan for a UI error based on the provided task and action history.

    Args:
        task (str): The task description that the robot was trying to complete.
        action_history (str): The history of actions taken by the robot.
        screenshot (str): base64-encoded screenshot of the current UI state.

    Returns:
        str: A JSON object containing the recovery plan.
    """
    model = OpenAIModel(
        client_args={
            "api_key": PROVIDER_API_KEY,
            "base_url": PROVIDER_API_BASE,
        },
        model_id=PROVIDER_VISION_MODEL,
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"text": RECOVERY_PLANNER_PROMPT},
                {
                    "image": {
                        "format": "jpeg",
                        "source": {
                            "bytes": take_screenshot(),
                        },
                    },
                },
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "I see this is the image of the current UI state. I will analyze it and generate a recovery plan once you provide the task and action history.",
                }
            ],
        },
    ]

    agent = Agent(
        model=model,
        messages=messages,
        tools=[step_execution_handler, take_screenshot],
    )
    response = agent(f"Task: {task}\nAction History: {action_history}")

    # TODO: Add response json to prompt and parse it
    return response


@tool(
    description="Execute the steps provided in the recovery plan to resolve the UI error.",
)
def step_execution_handler(
    step: str, step_history: str, process_goal: str, is_final: bool
) -> str:
    """
    Execute the step provided in the recovery plan to resolve the UI error.

    Args:
        step (str): The step to execute for advancing in the resolution of the UI error.
        step_history (str): The history of steps taken so far.
        process_goal (str): The overall goal of the process that the robot is trying to achieve.
        is_final (bool): Indicates if this is the final step in the recovery process.

    Returns:
        str: A confirmation message indicating the execution status (success|replan|abort).
    """
    model = OpenAIModel(
        client_args={
            "api_key": PROVIDER_API_KEY,
            "base_url": PROVIDER_API_BASE,
        },
        model_id=PROVIDER_VISION_MODEL,
    )

    messages = [
        {
            "role": "system",
            "content": RECOVERY_STEP_EXECUTION_PROMPT,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": {
                        "format": "jpeg",
                        "source": {"bytes": take_screenshot()},
                    },
                },
            ],
        },
        {
            "role": "assistant",
            "content": "I see this is the image of the current UI state. I will analyze it and execute the step once you provide the step, step history, and process goal.",
        },
    ]

    agent = Agent(
        model=model,
        messages=messages,
        # TODO: The take_screenshot tool won't work in this context because it will return text. We need an analyze image tool
        tools=[ui_tars, take_screenshot, ui_tars_execute],
    )
    response = agent(
        f"Step: {step}\nAction History: {step_history}\nProcess Goal: {process_goal}\nIs Final Step: {is_final}"
    )

    # TODO: Add response json to prompt and parse it
    return response


@tool(
    description="A element and action ground model for UI tasks.",
)
def ui_tars(task: str, action_history: str, screenshot: str) -> str:
    """
    Grounds an action for the current UI state using the UITARS ML model.

    Args:
        task (str): The task description (step).
        action_history (str): The history of actions taken by the robot.
        screenshot (str): base64-encoded screenshot of the current UI state.

    Returns:
        str: A string containing the RAW response from UITARS, which has the action to be performed on the screen.
    """
    # TODO

    instruction = f"""
Task: {task}
Action History: {action_history}
"""

    messages = [
        {
            "role": "user",
            "content": COMPUTER_USE_DOUBAO.format(instruction),
            "images": [screenshot],
        },
    ]

    response = httpx.post(
        url=f"{OLLAMA_URL}/api/chat",
        json={
            "model": "ui-tars-1.5-7b-q8_0",
            "messages": messages,
            "stream": False,
        },
    )

    return response.json().get("message", {}).get("content", "")


@tool(
    description="Execute the action on the UI element based on the TARS model.",
)
def ui_tars_execute(ui_tars_response: str) -> str:
    """
    Execute the action on the UI element based on the TARS model.

    Args:
        ui_tars_response (str): The RAW response from the `ui_tars` tool.

    Returns:
    """
    try:
        action = parse_action_to_structure_output(
            ui_tars_response,
            factor=1000,
            origin_resized_height=224,
            origin_resized_width=224,
        )[0]
        code = parsing_response_to_pyautogui_code(action, 224, 224)
        eval(code)
    except Exception as e:
        return f"Error executing action: {str(e)}"

    return "Action executed successfully."
