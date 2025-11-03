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
    UI_MID_AGENT,
)
from config import Config
from modules.uierror.agent_utils import (
    ensure_required_type,
    extract_agent_response_text,
)
from modules.uierror.prompts import (
    RECOVERY_DIRECT_PROMPT,
    STANDALONE_COMPUTER_USE_DOUBAO,
    UI_EXCEPTION_HANDLER,
    RECOVERY_PLANNER_PROMPT,
    RECOVERY_STEP_EXECUTION_PROMPT,
    COMPUTER_USE_DOUBAO,
)
from modules.uierror.uitars import (
    parse_action_to_structure_output,
    parsing_response_to_pyautogui_code,
)
from agent_tools.image import screenshot_bytes, take_screenshot, compare_images
from modules.uierror.templates import (
    RecoveryDirectReport,
    RecoveryPlannerReport,
    RecoveryStepExecutionResult,
    UiExceptionReport,
)


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
    ensure_required_type(action_history, "action_history", list)
    ensure_required_type(failed_activity, "failed_activity", dict)
    ensure_required_type(future_activities, "future_activities", list)
    ensure_required_type(variables, "variables", dict)

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
        if UI_MID_AGENT
        else [standalone_uitars]
    )

    agent = Agent(
        model=model,
        messages=messages,
        tools=[] + recovery_tools,
    )
    try:
        agent(
            f"Task: {task}\nAction History: {action_history}\nFailed Action: {failed_activity}\nFuture Activities: {future_activities}\nVariables: {variables}. DO NOT ASK FOR CONFIRMATION, execute the plan directly."
        )

        response = agent.structured_output(
            UiExceptionReport,
            "Given our conversation so far, please provide a structured recovery report.",
        )

        return [{"text": str(response)}]
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
    # future_activities: list,
    variables: dict,
) -> list:
    """
    This function is to be called by the ui_exception_handler tool to generate a recovery plan for a UI error.

    Args:
        task (str): The task description that the robot was trying to complete
        action_history (list): The history of actions taken by the robot (list)
        failed_activity (dict): The action that was expected to be performed but failed (dict)
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
    ensure_required_type(action_history, "action_history", list)
    ensure_required_type(failed_activity, "failed_activity", dict)
    ensure_required_type(variables, "variables", dict)

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

    agent = Agent(model=model, messages=messages, tools=[take_screenshot, ui_tars])
    try:
        agent(
            f"Task: {task}\nAction History: {action_history}\nFailed Action: {failed_activity}\nVariables: {variables}. DO NOT ASK FOR CONFIRMATION, execute the actions directly."
        )

        response = agent.structured_output(
            RecoveryDirectReport,
            "Given our conversation so far, please provide a structured recovery report.",
        )

        return [{"text": str(response)}]
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
    ensure_required_type(action_history, "action_history", list)
    ensure_required_type(failed_activity, "failed_activity", dict)
    ensure_required_type(future_activities, "future_activities", list)
    ensure_required_type(variables, "variables", dict)

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
        agent(
            f"Task: {task}\nAction History: {action_history}\nFailed Action: {failed_activity}\nFuture Activities: {future_activities}\nVariables: {variables}. DO NOT ASK FOR CONFIRMATION, execute the plan directly."
        )

        response = agent.structured_output(
            RecoveryPlannerReport,
            "Given our conversation so far, please provide a structured recovery plan.",
        )

        return [{"text": str(response)}]
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
        agent(
            f"Step: {step}\nStep History: {step_history}\nProcess Goal: {process_goal}\nVariables: {variables}\nIs Final Step: {is_final}"
        )

        response = agent.structured_output(
            RecoveryStepExecutionResult,
            "Given our conversation so far, please provide the structured step execution result.",
        )

        return [{"text": str(response)}]
    except Exception as e:
        return [{"text": str(e)}]


@tool(
    name="ui_tars",
    description="A element and action ground model for UI tasks.",
)
def ui_tars(
    task: str, step_history: list, variables: dict, expect_ui_change: bool
) -> list:
    """
    Grounds an action for the current UI state using the UITARS ML model.

    Args:
        task (str): The task description (step)
        step_history (list): The history of steps taken so far
        variables (dict): A dictionary of variables used in the process
        expect_ui_change(bool): Whether the action should trigger a noticable UI change (SSIM >= 0.95)

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

    before_screenshot = screenshot_bytes()

    messages = [
        {
            "role": "user",
            "content": [
                {"text": COMPUTER_USE_DOUBAO.format(instruction=instruction)},
                {
                    "type": "image",
                    "image": {
                        "format": "jpeg",
                        "source": {"bytes": before_screenshot},
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

        iteration = 1

        while True:
            ui_tars_response = ""
            try:
                ui_tars_response = response.message.get("content", "")[0].get(
                    "text", ""
                )
            except Exception:
                ui_tars_response = str(response)
                break

            try:
                action = parse_action_to_structure_output(
                    ui_tars_response,
                    origin_resized_height=1080,
                    origin_resized_width=1920,
                )[0]
                code = parsing_response_to_pyautogui_code(action, 1080, 1920)
                exec(code)
            except Exception as e:
                if iteration >= Config.MAX_UI_ACTION_RETRIES:
                    return [{"text": f"Error executing action: {str(e)}"}]
                response = agent("The action failed. Try again")
                iteration += 1
                continue

            if (
                compare_images(before_screenshot, expect_ui_change)
                or iteration >= Config.MAX_UI_ACTION_RETRIES
            ):
                break
            else:
                # Redefinition of response before starting the loop again.
                response = agent("The action failed. Try again")
            iteration += 1

        return (
            [{"text": "Action executed successfully."}]
            if iteration < Config.MAX_UI_ACTION_RETRIES
            else [{"text": "Action failed after maximum retries."}]
        )
    except Exception as e:
        return [{"text": str(e)}]


@tool(
    name="standalone_uitars",
    description="A element and action ground model for UI tasks.",
)
def standalone_uitars(
    task: str,
    action_history: list,
    failed_activity: dict,
    variables: dict,
) -> list:
    """
    This function is to be called by the ui_exception_handler tool to execute a recovery plan for a UI error.

    Args:
        task (str): The task description that the robot was trying to complete
        action_history (list): The history of actions taken by the robot (list)
        failed_activity (dict): The action that was expected to be performed but failed (dict)
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

    instruction = f"""
Task: {task}
Action History: {action_history}
Failed Action: {failed_activity}
Variables: {variables}
"""

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": STANDALONE_COMPUTER_USE_DOUBAO.format(
                        instruction=instruction
                    )
                },
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

        iteration = 0

        while True:
            iteration += 1
            if iteration > Config.MAX_ACTIONS_ALLOWED:
                return [{"text": "Exceeded maximum allowed actions."}]

            ui_tars_response = ""
            try:
                ui_tars_response = response.message.get("content", "")[0].get(
                    "text", ""
                )
            except Exception:
                ui_tars_response = str(response)
                break

            try:
                action = parse_action_to_structure_output(
                    ui_tars_response,
                    origin_resized_height=1080,
                    origin_resized_width=1920,
                )[0]
                code = parsing_response_to_pyautogui_code(action, 1080, 1920)

                if code == "DONE":
                    break

                exec(code)

                new_messages = [
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
                ]

                response = agent(
                    new_messages
                )  # Empty input since all context is in messages
            except Exception as _:
                response = agent("The action failed. Try again")
                continue

        conversation_history = list(
            map(
                lambda m: m["content"],
                filter(lambda m: m["role"] == "assistant", agent.messages),
            )
        )
        return conversation_history

    except Exception as e:
        return [{"text": str(e)}]
