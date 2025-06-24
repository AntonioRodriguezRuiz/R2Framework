from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from gateway.models import Module
from tools.links import ToolModuleLink
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column

class Tool(SQLModel, table=True):
    """
    Represents a tool that can be used in the system.
    """
    id: str = Field(..., description="Unique identifier for the tool.", primary_key=True)
    name: str = Field(..., description="Name of the tool.")
    description: Optional[str] = Field(None, description="Description of the tool, if available.")
    enabled: bool = Field(True, description="Indicates whether the tool is enabled or not.")
    implementation: str = Field(..., description="Function that implements the tool's logic.")
    uses: list["ToolUse"] = Relationship(back_populates="tool", sa_relationship_kwargs={"lazy": "joined"})
    # We define here the relations to modules to avoid circular imports
    modules: list[Module] = Relationship(back_populates="tools", sa_relationship_kwargs={"lazy": "joined"}, link_model=ToolModuleLink)

class ToolUse(SQLModel, table=True):
    """
    Represents a usage instance of a tool.
    """
    id: str = Field(..., description="Unique identifier for the tool use instance.", primary_key=True)
    tool: Tool = Relationship(back_populates="uses", sa_relationship_kwargs={"lazy": "joined"})
    module: Optional[Module] = Relationship(back_populates="tool_uses", sa_relationship_kwargs={"lazy": "joined"})
    timestamp: str = Field(..., description="Timestamp of when the tool was used.")
    parameters: Optional[dict] = Field(None, description="Parameters used when invoking the tool.", sa_column=Column(JSON))
    result: Optional[str] = Field(None, description="Result returned by the tool after execution.")

    class Config:
        arbitrary_types_allowed = True