from strands import Agent, tool
from strands.models.openai import OpenAIModel
from settings import (
    PROVIDER_API_BASE,
    PROVIDER_API_KEY,
    PROVIDER_MODEL,
    PROVIDER_VISION_MODEL,
    PROVIDER_VISION_TOOL_MODEL,
    PROVIDER_GROUNDING_MODEL,
    OLLAMA_URL,
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
) -> str:
    """
    Generate a recovery plan for a UI error based on the provided task and action history.

    Args:
        task (str): The task description that the robot was trying to complete.
        action_history (list): The history of actions taken by the robot.
        failed_activity (dict): The action that was expected to be performed but failed.
        future_activities (list): The list of future activities that the robot was planning to perform.
        screenshot (str): base64-encoded screenshot of the current UI state.
        variables (dict): A dictionary of variables used in the process, including the ones that may have already been used.

    Returns:
        str: A JSON object containing the recovery plan.
    """
    model = OpenAIModel(
        client_args={
            "api_key": PROVIDER_API_KEY,
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
    response = agent(
        f"Task: {task}\nAction History: {action_history}\nFailed Action: {failed_activity}\nFuture Activities: {future_activities}\nVariables: {variables}. DO NOT ASK FOR CONFIRMATION, execute the plan directly."
    )

    # TODO: Add response json to prompt and parse it
    return response


@tool(
    name="recovery_plan_generator",
    description="Generate a recovery plan for a UI error based on the provided task and action history.",
)
def recovery_agent(
    task: str,
    action_history: list,
    failed_activity: dict,
    future_activities: list,
    variables: dict,
) -> str:
    """
    This function is to be called by the ui_exception_handler tool to generate a recovery plan for a UI error.

    This is because current openrouter vision models do not support tool uses, so we need to generate a plan separately from the exception handler.

    Args:
        task (str): The task description that the robot was trying to complete.
        action_history (list): The history of actions taken by the robot.
        failed_activity (dict): The action that was expected to be performed but failed.
        future_activities (list): The list of future activities that the robot was planning to perform.
        variables (dict): A dictionary of variables used in the process, including the ones that may have already been used.

    Returns:
        str: A JSON object containing the recovery plan.
    """
    model = OpenAIModel(
        client_args={
            "api_key": PROVIDER_API_KEY,
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
    response = agent(
        f"Task: {task}\nAction History: {action_history}\nFailed Action: {failed_activity}\nFuture Activities: {future_activities}\nVariables: {variables}. DO NOT ASK FOR CONFIRMATION, execute the actions directly."
    )

    # TODO: Add response json to prompt and parse it
    return response


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
) -> str:
    """
    This function is to be called by the ui_exception_handler tool to generate a recovery plan for a UI error.

    This is because current openrouter vision models do not support tool uses, so we need to generate a plan separately from the exception handler.

    Args:
        task (str): The task description that the robot was trying to complete.
        action_history (list): The history of actions taken by the robot.
        failed_activity (dict): The action that was expected to be performed but failed.
        future_activities (list): The list of future activities that the robot was planning to perform.
        variables (dict): A dictionary of variables used in the process, including the ones that may have already been used.

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
    response = agent(
        f"Task: {task}\nAction History: {action_history}\nFailed Action: {failed_activity}\nFuture Activities: {future_activities}\nVariables: {variables}. DO NOT ASK FOR CONFIRMATION, execute the plan directly."
    )

    # TODO: Add response json to prompt and parse it
    return response


@tool(
    description="Execute the steps provided in the recovery plan to resolve the UI error.",
)
def step_execution_handler(
    step: str, step_history: str, process_goal: str, variables: dict, is_final: bool
) -> str:
    """
    Execute the step provided in the recovery plan to resolve the UI error.

    Args:
        step (str): The step to execute for advancing in the resolution of the UI error.
        step_history (str): The history of steps taken so far.
        process_goal (str): The overall goal of the process that the robot is trying to achieve.
        variables (dict): A dictionary of variables used in the process, including the ones that may have already been used.
        is_final (bool): Indicates if this is the final step in the recovery process.

    Returns:
        str: A confirmation message indicating the execution status (success|replan|abort).
    """
    model = OpenAIModel(
        client_args={
            "api_key": PROVIDER_API_KEY,
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
    response = agent(
        f"Step: {step}\nStep History: {step_history}\nProcess Goal: {process_goal}\nVariables: {variables}\nIs Final Step: {is_final}"
    )

    # TODO: Add response json to prompt and parse it
    return response


@tool(
    name="ui_tars",
    description="A element and action ground model for UI tasks.",
)
def ui_tars(task: str, step_history: str, variables: dict) -> str:
    """
    Grounds an action for the current UI state using the UITARS ML model.

    Args:
        task (str): The task description (step).
        step_history (str): The history of step taken so far to solve the error.
        screenshot (str): base64-encoded screenshot of the current UI state.
        variables (dict): A dictionary of variables used in the process, including the ones that may have already been used.

    Returns:
        str: A string containing the RAW response from UITARS, which has the action to be performed on the screen.
    """
    # TODO

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
        client_args={
            "api_key": PROVIDER_API_KEY,
            "base_url": OLLAMA_URL,
        },
        model_id=PROVIDER_GROUNDING_MODEL,
    )

    agent = Agent(
        model=model,
        messages=messages,
    )
    response = agent("")  # Empty input since all context is in messages

    ui_tars_response = response.message.get("content", "")[0].get("text", "")

    # @tool(
    #     name="ui_tars_execute",
    #     description="Execute the action on the UI element based on the TARS model.",
    # )
    # def ui_tars_execute(ui_tars_response: str) -> str:
    #     """
    #     Execute the action on the UI element based on the TARS model.

    #     Args:
    #         ui_tars_response (str): The RAW response from the `ui_tars` tool.

    #     Returns:
    #     """
    try:
        action = parse_action_to_structure_output(
            ui_tars_response,
            factor=1000,
            origin_resized_height=224,
            origin_resized_width=224,
        )[0]
        code = parsing_response_to_pyautogui_code(action, 224, 224)
        exec(code)
    except Exception as e:
        return f"Error executing action: {str(e)}"

    return "Action executed successfully."
