from strands import Agent, tool
from strands.models.openai import OpenAIModel
from settings import (
    PROVIDER_API_BASE,
    PROVIDER_API_KEY,
    FREE_PROVIDER_API_KEY,
    PROVIDER_MODEL,
    PROVIDER_VISION_MODEL,
    PROVIDER_VISION_TOOL_MODEL,
    PROVIDER_GROUNDING_MODEL,
    UI_ERROR_PLANNING,
)
from modules.uierror.prompts import (
    RECOVERY_DIRECT_PROMPT,
    UI_EXCEPTION_HANDLER,
    RECOVERY_PLANNER_PROMPT,
    RECOVERY_STEP_EXECUTION_PROMPT,
    COMPUTER_USE_DOUBAO,
)
from modules.uierror.uitars import (
    parse_action_to_structure_output,
    parsing_response_to_pyautogui_code,
)
from agent_tools.image import screenshot_bytes, take_screenshot


@tool(
    name="ui_exception_handler",
    description="Generate a recovery plan for a UI error based on the provided task and action history.",
)
def ui_exception_handler(
    task: str,
    action_history: list,
    failed_activity: dict,
    future_activities: list,
    variables: dict,
) -> list:
    """
    Generate a recovery plan for a UI error based on the provided task and action history.

    Args:
        task (str): The task description that the robot was trying to complete
        action_history (list): The history of actions taken by the robot (list)
        failed_activity (dict): The action that was expected to be performed but failed (dict)
        future_activities (list): The list of future activities the robot planned to perform (list)
        variables (dict): A dictionary of variables used in the process

    Returns:
        Dictionary containing status and tool response:
        {
            "toolUseId": "unique_id",
            "status": "success|error",
            "content": [{"text": "Recovery report"}]
        }

        Success: Returns a JSON-serializable report of the recovery in content[0]["text"].
        Error: Returns information about what went wrong.
    """
    # Validate inputs (fail fast if missing or wrong type)
    assert action_history is not None, "action_history is required"
    assert isinstance(action_history, list), "action_history must be a list"
    assert failed_activity is not None, "failed_activity is required"
    assert isinstance(failed_activity, dict), "failed_activity must be a dict"
    assert future_activities is not None, "future_activities is required"
    assert isinstance(future_activities, list), "future_activities must be a list"
    assert variables is not None, "variables is required"
    assert isinstance(variables, dict), "variables must be a dict"

    model = OpenAIModel(
        client_args={
            "api_key": FREE_PROVIDER_API_KEY,
            "base_url": PROVIDER_API_BASE,
        },
        model_id=PROVIDER_MODEL,
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"text": UI_EXCEPTION_HANDLER},
            ],
        },
    ]

    recovery_tools = (
        [recovery_plan_generator, step_execution_handler]
        if UI_ERROR_PLANNING
        else [recovery_agent]
    )

    agent = Agent(
        model=model,
        messages=messages,
        tools=[] + recovery_tools,
    )
    try:
        response = agent(
            f"Task: {task}\nAction History: {action_history}\nFailed Action: {failed_activity}\nFuture Activities: {future_activities}\nVariables: {variables}. DO NOT ASK FOR CONFIRMATION, execute the plan directly."
        )

        # Try to extract text content if available
        content_text = str(response)
        try:
            msg = getattr(response, "message", None)
            if msg:
                parts = []
                for c in msg.get("content", []):
                    if c.get("text"):
                        parts.append(c.get("text"))
                if parts:
                    content_text = "\n".join(parts)
        except Exception:
            pass

        return [{"text": content_text}]
    except Exception as e:
        return [{"text": str(e)}]


@tool(
    name="recovery_agent",
    description="Execute a recovery for a UI error based on the provided task and action history.",
)
def recovery_agent(
    task: str,
    action_history: list,
    failed_activity: dict,
    future_activities: list,
    variables: dict,
) -> list:
    """
    This function is to be called by the ui_exception_handler tool to generate a recovery plan for a UI error.

    Args:
        task (str): The task description that the robot was trying to complete
        action_history (list): The history of actions taken by the robot (list)
        failed_activity (dict): The action that was expected to be performed but failed (dict)
        future_activities (list): The list of future activities the robot planned to perform (list)
        variables (dict): A dictionary of variables used in the process

    Returns:
        Dictionary containing status and tool response:
        {
            "toolUseId": "unique_id",
            "status": "success|error",
            "content": [{"text": "Recovery plan or error message"}]
        }

        Success: Returns a textual recovery plan or JSON-serializable plan in content[0]["text"].
        Error: Returns information about what went wrong.
    """
    # Validate inputs (fail fast if missing or wrong type)
    assert action_history is not None, "action_history is required"
    assert isinstance(action_history, list), "action_history must be a list"
    assert failed_activity is not None, "failed_activity is required"
    assert isinstance(failed_activity, dict), "failed_activity must be a dict"
    assert future_activities is not None, "future_activities is required"
    assert isinstance(future_activities, list), "future_activities must be a list"
    assert variables is not None, "variables is required"
    assert isinstance(variables, dict), "variables must be a dict"

    model = OpenAIModel(
        client_args={
            "api_key": FREE_PROVIDER_API_KEY,
            "base_url": PROVIDER_API_BASE,
        },
        model_id=PROVIDER_VISION_TOOL_MODEL,
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"text": RECOVERY_DIRECT_PROMPT},
                {
                    "image": {
                        "format": "jpeg",
                        "source": {
                            "bytes": screenshot_bytes(),
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
                    "text": "I see this is the image of the current UI state. I will analyze it and create a recovery plan once you provide the task and action history.",
                }
            ],
        },
    ]

    agent = Agent(
        model=model,
        messages=messages,
        tools=[take_screenshot, ui_tars],
    )
    try:
        response = agent(
            f"Task: {task}\nAction History: {action_history}\nFailed Action: {failed_activity}\nFuture Activities: {future_activities}\nVariables: {variables}. DO NOT ASK FOR CONFIRMATION, execute the actions directly."
        )

        content_text = str(response)
        try:
            msg = getattr(response, "message", None)
            if msg:
                parts = []
                for c in msg.get("content", []):
                    if c.get("text"):
                        parts.append(c.get("text"))
                if parts:
                    content_text = "\n".join(parts)
        except Exception:
            pass

        return [{"text": content_text}]
    except Exception as e:
        return [{"text": str(e)}]


@tool(
    name="recovery_plan_generator",
    description="Generate a recovery plan for a UI error based on the provided task and action history.",
)
def recovery_plan_generator(
    task: str,
    action_history: list,
    failed_activity: dict,
    future_activities: list,
    variables: dict,
) -> list:
    """
    This function is to be called by the ui_exception_handler tool to generate a recovery plan for a UI error.

    Args:
        task (str): The task description that the robot was trying to complete
        action_history (list): The history of actions taken by the robot (list)
        failed_activity (dict): The action that was expected to be performed but failed (dict)
        future_activities (list): The list of future activities the robot planned to perform (list)
        variables (dict): A dictionary of variables used in the process

    Returns:
        Dictionary containing status and tool response:
        {
            "toolUseId": "unique_id",
            "status": "success|error",
            "content": [{"text": "Recovery plan or error message"}]
        }

        Success: Returns a textual recovery plan or JSON-serializable plan in content[0]["text"].
        Error: Returns information about what went wrong.
    """
    # Validate inputs (fail fast if missing or wrong type)
    assert action_history is not None, "action_history is required"
    assert isinstance(action_history, list), "action_history must be a list"
    assert failed_activity is not None, "failed_activity is required"
    assert isinstance(failed_activity, dict), "failed_activity must be a dict"
    assert future_activities is not None, "future_activities is required"
    assert isinstance(future_activities, list), "future_activities must be a list"
    assert variables is not None, "variables is required"
    assert isinstance(variables, dict), "variables must be a dict"

    model = OpenAIModel(
        client_args={
            "api_key": FREE_PROVIDER_API_KEY,
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
                            "bytes": screenshot_bytes(),
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
                    "text": "I see this is the image of the current UI state. I will analyze it and create a recovery plan once you provide the task and action history.",
                }
            ],
        },
    ]

    agent = Agent(
        model=model,
        messages=messages,
    )
    try:
        response = agent(
            f"Task: {task}\nAction History: {action_history}\nFailed Action: {failed_activity}\nFuture Activities: {future_activities}\nVariables: {variables}. DO NOT ASK FOR CONFIRMATION, execute the plan directly."
        )

        content_text = str(response)
        try:
            msg = getattr(response, "message", None)
            if msg:
                parts = []
                for c in msg.get("content", []):
                    if c.get("text"):
                        parts.append(c.get("text"))
                if parts:
                    content_text = "\n".join(parts)
        except Exception:
            pass

        return [{"text": content_text}]
    except Exception as e:
        return [{"text": str(e)}]


@tool(
    description="Execute the steps provided in the recovery plan to resolve the UI error.",
)
def step_execution_handler(
    step: str,
    step_history: list,
    process_goal: str,
    variables: dict,
    is_final: bool,
) -> list:
    """
    Execute the step provided in the recovery plan to resolve the UI error.

    Args:
        step (str): The step to execute for advancing the resolution of the UI error
        step_history (list): The history of steps taken so far
        process_goal (str): The overall goal of the process the robot is trying to achieve
        variables (dict): A dictionary of variables used in the process
        is_final (bool): Boolean, indicates if this is the final step

    Returns:
        Dictionary containing status and tool response:
        {
            "toolUseId": "unique_id",
            "status": "success|error",
            "content": [{"text": "Execution result, or 'replan'/'abort' info"}]
        }

        Success: Returns confirmation of execution or 'replan'/'abort' instruction.
        Error: Returns information about what went wrong.
    """
    step_history = step_history or ""
    process_goal = process_goal or ""
    variables = variables or {}

    model = OpenAIModel(
        client_args={
            "api_key": FREE_PROVIDER_API_KEY,
            "base_url": PROVIDER_API_BASE,
        },
        model_id=PROVIDER_VISION_TOOL_MODEL,
    )

    messages = [
        {
            "role": "system",
            "content": [
                {"text": RECOVERY_STEP_EXECUTION_PROMPT},
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": {
                        "format": "jpeg",
                        "source": {"bytes": screenshot_bytes()},
                    },
                },
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "text": "I see this is the image of the current UI state. I will analyze it and execute the step once you provide the step, step history, and process goal.",
                }
            ],
        },
    ]

    agent = Agent(
        model=model,
        messages=messages,
        tools=[ui_tars, take_screenshot],
    )
    try:
        response = agent(
            f"Step: {step}\nStep History: {step_history}\nProcess Goal: {process_goal}\nVariables: {variables}\nIs Final Step: {is_final}"
        )

        content_text = str(response)
        try:
            msg = getattr(response, "message", None)
            if msg:
                parts = []
                for c in msg.get("content", []):
                    if c.get("text"):
                        parts.append(c.get("text"))
                if parts:
                    content_text = "\n".join(parts)
        except Exception:
            pass

        return [{"text": content_text}]
    except Exception as e:
        return [{"text": str(e)}]


@tool(
    name="ui_tars",
    description="A element and action ground model for UI tasks.",
)
def ui_tars(task: str, step_history: list, variables: dict) -> list:
    """
    Grounds an action for the current UI state using the UITARS ML model.

    Args:
        task (str): The task description (step)
        step_history (list): The history of steps taken so far
        variables (dict): A dictionary of variables used in the process

    Returns:
        Dictionary containing status and tool response:
        {
            "toolUseId": "unique_id",
            "status": "success|error",
            "content": [{"text": "Raw UITARS response or error message"}]
        }

        Success: Returns the raw response from the grounding model and attempts to execute the produced action.
        Error: Returns information about what went wrong during parsing or execution.
    """
    step_history = step_history or ""
    variables = variables or {}

    instruction = f"""
Task: {task}
Step History: {step_history}
Variables: {variables}
"""

    messages = [
        {
            "role": "user",
            "content": [
                {"text": COMPUTER_USE_DOUBAO.format(instruction=instruction)},
                {
                    "type": "image",
                    "image": {
                        "format": "jpeg",
                        "source": {"bytes": screenshot_bytes()},
                    },
                },
            ],
        },
    ]

    model = OpenAIModel(
        client_args={"api_key": PROVIDER_API_KEY, "base_url": PROVIDER_API_BASE},
        model_id=PROVIDER_GROUNDING_MODEL,
    )

    agent = Agent(
        model=model,
        messages=messages,
    )
    try:
        response = agent("")  # Empty input since all context is in messages

        ui_tars_response = ""
        try:
            ui_tars_response = response.message.get("content", "")[0].get("text", "")
        except Exception:
            ui_tars_response = str(response)

        try:
            action = parse_action_to_structure_output(
                ui_tars_response,
                origin_resized_height=1080,
                origin_resized_width=1920,
            )[0]
            code = parsing_response_to_pyautogui_code(action, 1080, 1920)
            exec(code)
        except Exception as e:
            return [{"text": f"Error executing action: {str(e)}"}]

        return [{"text": "Action executed successfully."}]
    except Exception as e:
        return [{"text": str(e)}]
