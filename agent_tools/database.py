from strands import tool
from database.general import general_engine
from gateway.models import Module
from sqlmodel import Session, select


@tool(name="available_modules", description="List all available modules in the system.")
def available_modules() -> list:
    """
    List all available modules in the system.

    Args:
        (no inputs required) - tool input can be empty

    Returns:
        Dictionary containing status and tool response:
        {
            "toolUseId": "unique_id",
            "status": "success|error",
            "content": [{"json": [<module objects>]}]
        }

        Success: Returns a JSON list of available modules under content[0]["json"].
        Error: Returns information about what went wrong.
    """
    try:
        with Session(general_engine) as session:
            modules = session.exec(select(Module)).unique()
            modules_json = [module.to_json() for module in modules]

        # Return only the 'content' value as requested by the new contract
        return [{"json": modules_json}]
    except Exception as e:
        return [{"text": str(e)}]


@tool(
    name="register_solution",
    description="Register a new solution by an agentic module.",
)
def register_solution(solution_description: str, module_name: str) -> list:
    """
    Args:
        solution_description (str): Text describing the solution to register
        module_name (str): Name of the module registering the solution

    Returns:
        Dictionary containing status and tool response (Not implemented yet):
        {
            "toolUseId": "unique_id",
            "status": "error",
            "content": [{"text": "Not implemented"}]
        }

    Note: This function needs to be migrated to accept ToolUse and return ToolResult. Currently raises NotImplementedError.
    """
    # Not implemented — return the content structure indicating this
    return [{"text": "Not implemented"}]


@tool(
    description="Register a new plan by an agentic module.",
)
def register_plan(plan_description: str, module_name: str) -> list:
    """
    Register a new plan by an agentic module.

    Args:
        plan_description (str): Text describing the plan to register
        module_name (str): Name of the module registering the plan

    Returns:
        Dictionary containing status and tool response (Not implemented yet):
        {
            "toolUseId": "unique_id",
            "status": "error",
            "content": [{"text": "Not implemented"}]
        }

    Note: This function needs to be migrated to accept ToolUse and return ToolResult. Currently raises NotImplementedError.
    """
    # Not implemented — return the content structure indicating this
    return [{"text": "Not implemented"}]
