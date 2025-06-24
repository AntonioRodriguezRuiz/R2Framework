from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from gateway.models import Module
from tools.links import ToolModuleLink
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column
import uuid

class Tool(SQLModel, table=True):
    """
    Represents a tool that can be used in the system.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the tool.", primary_key=True)
    name: str = Field(..., description="Name of the tool.")
    description: Optional[str] = Field(None, description="Description of the tool, if available.")
    enabled: bool = Field(True, description="Indicates whether the tool is enabled or not.")
    implementation: str = Field(..., description="Function that implements the tool's logic.")
    # We define here the relations to modules to avoid circular imports
    modules: list[Module] = Relationship(back_populates="tools", sa_relationship_kwargs={"lazy": "joined"}, link_model=ToolModuleLink)

class ToolUse(SQLModel, table=True):
    """
    Represents a usage instance of a tool.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the tool use instance.", primary_key=True)
    tool_id: uuid.UUID = Field(..., foreign_key="tool.id", description="ID of the tool that was used.")
    action_id: uuid.UUID = Field(..., foreign_key="executedaction.id", description="ID of the action that was executed using the tool.")
    timestamp: str = Field(..., description="Timestamp of when the tool was used.")
    parameters: Optional[dict] = Field(None, description="Parameters used when invoking the tool.", sa_column=Column(JSON))
    result: Optional[str] = Field(None, description="Result returned by the tool after execution.")

    class Config:
        arbitrary_types_allowed = True