"""
Hardcoded populator for registering framework Agents into the database.

Further down the road this should be completely removed and loaded though a dump as the default agents. Contrary to tools, these are not dynamic

Registered Agents:
1. Gateway Orchestrator Agent            (routes external exceptions)
2. UI Exception Handler Agent            (top-level UI recovery agent)
3. UI Direct Recovery Agent              (sub-agent for direct recovery)
4. UI Recovery Plan Generator Agent      (sub-agent that plans recovery)
5. UI Step Execution Agent               (sub-agent that executes planned steps)
6. UI UITARS Agent                       (sub-agent for UI grounding)
7. UI Standalone UITARS Agent            (sub-agent for standalone action grounding)

Notes:
- Idempotent: agents are only created if they do not already exist (matched by name).
- Tools must have been populated previously (populate_tools) or they will be skipped.
- A default Router is created if none exists (uses settings fallback values).
- Response model paths are stored as import strings for dynamic loading at runtime.
"""

from __future__ import annotations

from typing import List, Optional

from sqlmodel import Session, select

from database.agents.models import (
    Agent,
    AgentTool,
    AgentType,
    Argument,
    SubAgent,
)
from database.provider.models import Router
from database.tools.models import Tool

# Prompts & response models
from gateway.prompts import GATEWAY_ORCHESTRATOR_PROMPT
from modules.uierror.prompts import (
    RECOVERY_DIRECT_PROMPT,
    RECOVERY_PLANNER_PROMPT,
    RECOVERY_STEP_EXECUTION_PROMPT,
    UI_EXCEPTION_HANDLER,
)

# Settings (fallbacks if not present)
try:
    from settings import (
        PROVIDER_GROUNDING_MODEL,
        PROVIDER_MODEL,
        PROVIDER_VISION_MODEL,
        PROVIDER_VISION_TOOL_MODEL,
    )
except Exception:
    # Fallback defaults (non-secure placeholders)
    PROVIDER_MODEL = "gpt-4o-mini"
    PROVIDER_VISION_MODEL = "gpt-4o-vision-mini"
    PROVIDER_VISION_TOOL_MODEL = "gpt-4o-vision-tool"
    PROVIDER_GROUNDING_MODEL = "gpt-4o-grounding"


def _get_router_by_model(session: Session, model_name: str) -> Router:
    """
    Return an existing Router for the given model_name or panics
    (uses FREE_PROVIDER_API_KEY except for grounding model which may use PROVIDER_API_KEY).
    """
    router = session.exec(select(Router).where(Router.model_name == model_name)).first()
    if router:
        return router
    else:
        raise ValueError(
            f"[populate_agents] Error: No Router found for model '{model_name}'. Please create it first."
        )


def _argument(
    name: str,
    description: str,
    py_type: str,
    json_type: str,
) -> Argument:
    """Helper to create an Argument instance."""
    return Argument(
        name=name,
        description=description,
        type=py_type,
        json_type=json_type,
    )


def _attach_tools(
    session: Session, agent: Agent, tool_names: List[str], limit: Optional[int]
) -> None:
    """
    Attach tools (by name) to an Agent via AgentTool association.
    Skips missing tools but logs a warning.
    """
    for tool_name in tool_names:
        tool = session.exec(select(Tool).where(Tool.name == tool_name)).first()
        if not tool:
            print(
                f"[populate_agents] Warning: Tool '{tool_name}' not found. Skipping for agent '{agent.name}'."
            )
            continue

        # Check if already associated
        if any(at.tool.id == tool.id for at in agent.tools):
            continue

        session.add(
            AgentTool(
                agent=agent,
                agent_id=agent.id,
                tool=tool,
                tool_id=tool.id,
                limit=limit,
                required=False,
            )
        )


def _create_agent(
    session: Session,
    name: str,
    description: str,
    prompt: str,
    response_model: str | None,
    args: List[Argument],
    router: Router,
    agent_type: AgentType,
    input_type: Agent.InputType = Agent.InputType.TEXT,
    enabled: bool = True,
) -> Agent:
    """Create and persist an Agent if it doesn't already exist."""
    existing = session.exec(select(Agent).where(Agent.name == name)).first()
    if existing:
        return existing

    agent = Agent(
        name=name,
        description=description,
        prompt=prompt,
        response_model=response_model,
        input_type=input_type,
        enabled=enabled,
        router=router,
        type=agent_type,
        arguments=args,
    )
    session.add(agent)
    session.commit()
    session.refresh(agent)
    print(f"[populate_agents] Created agent '{name}'.")
    return agent


def _create_sub_agent(
    session: Session, parent: Agent, child: Agent, limit: Optional[int]
) -> None:
    """Create a SubAgent relationship if not present."""
    existing = session.exec(
        select(SubAgent).where(
            SubAgent.parent_agent == parent, SubAgent.child_agent == child
        )
    ).first()
    if existing:
        return
    session.add(
        SubAgent(
            parent_agent_id=parent.id,
            parent_agent=parent,
            child_agent_id=child.id,
            child_agent=child,
            limit=limit,
        )
    )


def populate_agents(engine) -> None:
    """
    Populate the database with framework agents and their relationships.
    """
    with Session(engine) as session:
        # Resolve routers per model requirement (created on demand if missing)
        gateway_router = _get_router_by_model(session, PROVIDER_MODEL)
        ui_handler_router = _get_router_by_model(session, PROVIDER_MODEL)
        direct_recovery_router = _get_router_by_model(
            session, PROVIDER_VISION_TOOL_MODEL
        )
        plan_generator_router = _get_router_by_model(session, PROVIDER_VISION_MODEL)
        step_execution_router = _get_router_by_model(
            session, PROVIDER_VISION_TOOL_MODEL
        )
        uitars_router = _get_router_by_model(session, PROVIDER_GROUNDING_MODEL)
        standalone_uitars_router = _get_router_by_model(
            session, PROVIDER_GROUNDING_MODEL
        )

        # Gateway Agent
        gateway_args = [
            _argument(
                "code",
                "Raw error code or identifier reported by the RPA system.",
                "str",
                "string",
            ),
            _argument(
                "variables",
                "Dictionary of runtime variables at error time.",
                "dict",
                "object",
            ),
            _argument(
                "details",
                "Additional structured details or metadata about the error.",
                "dict",
                "object",
            ),
        ]

        gateway_agent = _create_agent(
            session=session,
            name="Gateway Orchestrator",
            description="Central orchestrator that standardizes and routes external RPA error notifications.",
            prompt=GATEWAY_ORCHESTRATOR_PROMPT,
            response_model="gateway.templates.ResponseToRPA",
            args=gateway_args,
            router=gateway_router,
            agent_type=AgentType.GatewayAgent,
        )

        _attach_tools(
            session,
            gateway_agent,
            [
                "route_to_human",
            ],
            None,
        )

        # UI Exception Handler (Top-level)
        ui_handler_args = [
            _argument(
                "task",
                "Original business task the robot was executing.",
                "str",
                "string",
            ),
            _argument(
                "action_history",
                "List of executed actions prior to failure.",
                "list",
                "array",
            ),
            _argument(
                "failed_activity",
                "The action that failed causing the exception.",
                "dict",
                "object",
            ),
            _argument(
                "future_activities",
                "Planned upcoming actions after failure.",
                "list",
                "array",
            ),
            _argument(
                "variables", "Runtime variables relevant to the task.", "dict", "object"
            ),
        ]

        ui_exception_handler_agent = _create_agent(
            session=session,
            name="UI Exception Handler",
            description="""## Agent description
            Module responsible for managing UI-related errors.
            This module has access to the current UI state via screenshots and is provided with visual information about the moment where execution failed.
            It specializes in identifying and resolving issues related to user interface interactions, element detection, and visual validation failures.

            ## Module restrictions
            - Must have access to current UI via screenshots
            - Must be provided visual information about execution failure moment

            ## Example error types
            - Error raised when a UI element cannot be located
            """,
            prompt=UI_EXCEPTION_HANDLER,
            response_model="modules.uierror.templates.UiExceptionReport",
            args=ui_handler_args,
            router=ui_handler_router,
            agent_type=AgentType.ErrorAgent,
            input_type=Agent.InputType.TEXT,
        )

        _attach_tools(
            session, ui_exception_handler_agent, ["compute_continuation_activity"], None
        )

        # Direct Recovery Agent
        direct_recovery_args = [
            _argument("task", "Task description at failure time.", "str", "string"),
            _argument("action_history", "Prior executed actions.", "list", "array"),
            _argument("failed_activity", "Failed action structure.", "dict", "object"),
            _argument("variables", "Execution variables.", "dict", "object"),
        ]
        direct_recovery_agent = _create_agent(
            session=session,
            name="UI Direct Recovery",
            description="Performs immediate direct UI recovery using vision and tool models.",
            prompt=RECOVERY_DIRECT_PROMPT,
            response_model="modules.uierror.templates.RecoveryDirectReport",
            args=direct_recovery_args,
            router=direct_recovery_router,
            agent_type=AgentType.GuiAgent,
            input_type=Agent.InputType.IMAGETEXT,
            enabled=False,
        )
        _attach_tools(
            session,
            direct_recovery_agent,
            [
                "take_screenshot",
            ],
            None,
        )

        # Recovery Plan Generator
        plan_generator_args = [
            _argument("task", "Task description at failure time.", "str", "string"),
            _argument("action_history", "Prior executed actions.", "list", "array"),
            _argument("failed_activity", "Failed action structure.", "dict", "object"),
            _argument(
                "future_activities", "Upcoming planned actions.", "list", "array"
            ),
            _argument("variables", "Execution variables.", "dict", "object"),
        ]
        plan_generator_agent = _create_agent(
            session=session,
            name="UI Recovery Planner",
            description="Generates a multi-step recovery plan for a UI failure.",
            prompt=RECOVERY_PLANNER_PROMPT,
            response_model="modules.uierror.templates.RecoveryPlannerReport",
            args=plan_generator_args,
            router=plan_generator_router,
            agent_type=AgentType.GuiAgent,
            input_type=Agent.InputType.IMAGETEXT,
            enabled=False,
        )
        _attach_tools(session, plan_generator_agent, ["take_screenshot"], None)

        # Step Execution Agent
        step_execution_args = [
            _argument("step", "Current recovery step to execute.", "str", "string"),
            _argument(
                "step_history", "Previously executed recovery steps.", "list", "array"
            ),
            _argument("process_goal", "Overall goal of the process.", "str", "string"),
            _argument("variables", "Execution variables.", "dict", "object"),
            _argument("is_final", "Whether this is the final step.", "bool", "boolean"),
        ]
        step_execution_agent = _create_agent(
            session=session,
            name="UI Step Executor",
            description="Executes individual planned recovery steps and validates outcomes.",
            prompt=RECOVERY_STEP_EXECUTION_PROMPT,
            response_model="modules.uierror.templates.RecoveryStepExecutionResult",
            args=step_execution_args,
            router=step_execution_router,
            agent_type=AgentType.GuiAgent,
            input_type=Agent.InputType.IMAGETEXT,
            enabled=False,
        )
        _attach_tools(session, step_execution_agent, ["take_screenshot"], None)

        # UITARS Agent
        uitars_args = [
            _argument("task", "Action or UI step to ground.", "str", "string"),
            _argument("step_history", "Previously executed steps.", "list", "array"),
            _argument("variables", "Execution variables.", "dict", "object"),
            _argument(
                "expect_ui_change",
                "Whether an observable UI change is expected.",
                "bool",
                "boolean",
            ),
        ]
        uitars_agent = _create_agent(
            session=session,
            name="UI UITARS Grounding",
            description="Grounds UI actions using UITARS model and executes them.",
            prompt="Ground and execute UI actions using provided context and screenshots.",
            response_model=None,
            args=uitars_args,
            router=uitars_router,
            agent_type=AgentType.GuiAgent,
            input_type=Agent.InputType.IMAGETEXT,
        )
        _attach_tools(session, uitars_agent, ["take_screenshot"], None)

        # Standalone UITARS Agent
        standalone_uitars_args = [
            _argument(
                "task", "Task description the robot was attempting.", "str", "string"
            ),
            _argument(
                "action_history", "History of executed actions.", "list", "array"
            ),
            _argument("failed_activity", "Failed action structure.", "dict", "object"),
            _argument("variables", "Execution variables.", "dict", "object"),
        ]
        standalone_uitars_agent = _create_agent(
            session=session,
            name="UI Standalone UITARS",
            description="Executes recovery directly via iterative UITARS grounding without planning.",
            prompt="Iteratively ground and execute UI actions until task recovered or attempts exhausted.",
            response_model=None,
            args=standalone_uitars_args,
            router=standalone_uitars_router,
            agent_type=AgentType.GuiAgent,
            input_type=Agent.InputType.IMAGETEXT,
        )
        _attach_tools(session, standalone_uitars_agent, [], None)

        _create_sub_agent(session, gateway_agent, ui_exception_handler_agent, 1)
        # Build sub-agent hierarchy under UI Exception Handler
        _create_sub_agent(session, ui_exception_handler_agent, direct_recovery_agent, 1)
        _create_sub_agent(session, ui_exception_handler_agent, plan_generator_agent, 1)
        _create_sub_agent(session, ui_exception_handler_agent, step_execution_agent, 1)
        _create_sub_agent(session, direct_recovery_agent, uitars_agent, 1)
        _create_sub_agent(session, step_execution_agent, uitars_agent, 1)
        _create_sub_agent(
            session, ui_exception_handler_agent, standalone_uitars_agent, 1
        )

        session.commit()
        print("[populate_agents] Agent population complete.")
