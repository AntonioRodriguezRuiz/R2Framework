from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
import uuid

class ToolModuleLink(SQLModel, table=True):
    """
    Represents a link between a ToolUse and a Module.
    This is used to avoid circular imports.
    """
    tool_id: uuid.UUID = Field(..., foreign_key="tool.id", primary_key=True)
    module_id: uuid.UUID = Field(..., foreign_key="module.id", primary_key=True)