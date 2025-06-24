from sqlmodel import SQLModel, Field

class ToolModuleLink(SQLModel, table=True):
    """
    Represents a link between a ToolUse and a Module.
    This is used to avoid circular imports.
    """
    tool_use_id: str = Field(..., foreign_key="tooluse.id", primary_key=True)
    module_id: str = Field(..., foreign_key="module.id", primary_key=True)
