from strands import tool
from database.general import general_engine
from gateway.models import Module
from sqlmodel import Session, select


@tool(description="List all available modules in the system.")
def available_modules() -> list[str]:
    """
    List all available modules in the system.

    Returns:
        list[str]: A list of module names.
    """
    with Session(general_engine) as session:
        modules = session.exec(select(Module)).unique()
        return [module.to_json() for module in modules]


@tool(
    description="Register a new solution by an agentic module.",
)
def register_solution(solution_description: str, module_name: str) -> str:
    # TODO
    pass


@tool(
    description="Register a new plan by an agentic module.",
)
def register_plan(plan_description: str, module_name: str) -> str:
    """
    Register a new plan by an agentic module.

    Args:
        plan_description (str): The description of the plan to be registered.
        module_name (str): The name of the module registering the plan.

    Returns:
        str: Confirmation message indicating the registration status.
    """
    # TODO
    pass
