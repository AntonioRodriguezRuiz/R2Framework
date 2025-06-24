# Defines the data models for the gateway service

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from gateway.enums import ExceptionType
from tools.links import ToolModuleLink

class Module(SQLModel, table=True):
    """
    Represents a error resolution module.
    """
    id: str = Field(..., description="Unique identifier for the module.", primary_key=True)
    timestamp: str = Field(datetime.now(), description="Timestamp of when the exception record was created.")
    name: str = Field(..., description="Name of the module.")
    description: str = Field(..., description="Description of the module, if available.")
    enabled: bool = Field(True, description="Indicates whether the module is enabled or not.")
    routing_tool: "Tool" = Relationship(sa_relationship_kwargs={"lazy": "joined"})
    # restrictions: Optional[list[str]] = Field(None, description="List of restrictions for the module, if any. (eg. 'no access to UI')")
    tools: list["Tool"] = Relationship(back_populates="modules", sa_relationship_kwargs={"lazy": "joined"}, link_model=ToolModuleLink) # ignore: type
    tool_uses: list["ToolUse"] = Relationship(back_populates="module", sa_relationship_kwargs={"lazy": "joined"}) # ignore: type
    audits: list["Audit"] = Relationship(back_populates="module", sa_relationship_kwargs={"lazy": "joined"}) # ignore: type

class RobotException(SQLModel, table=True):
    """
    Represents an exception to be routed for resolution by the gateway service.
    """
    id: str = Field(..., description="Unique identifier for the exception.", primary_key=True)
    timestamp: str = Field(datetime.now(), description="Timestamp of when the exception record was created.")
    code: str = Field(..., description="The error code associated with the exception.")
    exception_type: ExceptionType = Field(..., description="The type of exception")
    message: str = Field(..., description="A human-readable message describing the error.")
    details: Optional[str] = Field(None, description="Additional details about the error, if available.")
    audit: Optional["Audit"] = Relationship(back_populates="exception", sa_relationship_kwargs={"lazy": "joined"})

class Result(SQLModel, table=True):
    """
    Represents the result of an exception resolve operation.
    """
    id: str = Field(..., description="Unique identifier for the result.", primary_key=True)
    timestamp: str = Field(datetime.now(), description="Timestamp of when the exception record was created.")
    solved: bool = Field(..., description="Indicates whether the exception was successfully resolved.")
    has_fix: bool = Field(..., description="Indicates whether a fix was applied to the exception.")
    audit: Optional["Audit"] = Relationship(back_populates="result", sa_relationship_kwargs={"lazy": "joined"})


class Audit(SQLModel, table=True):
    """
    Represents an audit record for the routing of an Exception.
    """
    id: str = Field(..., description="Unique identifier for the audit record.", primary_key=True)
    timestamp: str = Field(datetime.now(), description="Timestamp of when the exception record was created.")
    reasoning: str = Field(..., description="The reasoning behind the routing decision.")
    module: Module = Relationship(back_populates="audits", sa_relationship_kwargs={"lazy": "joined"})
    result: Optional[Result] = Relationship(back_populates="audit", sa_relationship_kwargs={"lazy": "joined"})
    exception: RobotException = Relationship(back_populates="audit", sa_relationship_kwargs={"lazy": "joined"})