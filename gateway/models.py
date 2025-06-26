# Defines the data models for the gateway service

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from gateway.enums import ExceptionType
from agent_tools.links import ToolModuleLink
import uuid


class Module(SQLModel, table=True):
    """
    Represents a error resolution module.
    """

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for the module.",
        primary_key=True,
    )
    timestamp: str = Field(
        datetime.now(),
        description="Timestamp of when the exception record was created.",
    )
    name: str = Field(..., description="Name of the module.")
    description: str = Field(
        ..., description="Description of the module, if available."
    )
    enabled: bool = Field(
        True, description="Indicates whether the module is enabled or not."
    )
    routing_tool: str = Field(
        ...,
        description="The name of the tool used for routing exceptions to this module. This should be the name of a tool that is registered in the system.",
    )
    # restrictions: Optional[list[str]] = Field(None, description="List of restrictions for the module, if any. (eg. 'no access to UI')")
    tools: list["Tool"] = Relationship(
        back_populates="modules",
        sa_relationship_kwargs={"lazy": "joined"},
        link_model=ToolModuleLink,
    )  # ignore: type

    def to_json(self) -> dict:
        """Convert the model to a dictionary structure."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "routing_tool": self.routing_tool,
            "tools": [
                str(tool.id) if hasattr(tool, "id") else tool for tool in self.tools
            ]
            if self.tools
            else [],
        }


class RobotException(SQLModel, table=True):
    """
    Represents an exception to be routed for resolution by the gateway service.
    """

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for the exception.",
        primary_key=True,
    )
    timestamp: str = Field(
        datetime.now(),
        description="Timestamp of when the exception record was created.",
    )
    code: str = Field(..., description="The error code associated with the exception.")
    exception_type: ExceptionType = Field(..., description="The type of exception")
    message: str = Field(
        ..., description="A human-readable message describing the error."
    )
    details: Optional[str] = Field(
        None, description="Additional details about the error, if available."
    )

    def to_json(self) -> dict:
        """Convert the model to a dictionary structure."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp,
            "code": self.code,
            "exception_type": self.exception_type.value
            if self.exception_type
            else None,
            "message": self.message,
            "details": self.details,
        }


class Result(SQLModel, table=True):
    """
    Represents the result of an exception resolve operation.
    """

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for the result.",
        primary_key=True,
    )
    timestamp: str = Field(
        datetime.now(),
        description="Timestamp of when the exception record was created.",
    )
    solved: bool = Field(
        ..., description="Indicates whether the exception was successfully resolved."
    )
    has_fix: bool = Field(
        ..., description="Indicates whether a fix was applied to the exception."
    )
    audit_id: uuid.UUID = Field(
        ...,
        foreign_key="audit.id",
        description="ID of the audit record associated with this result.",
    )

    def to_json(self) -> dict:
        """Convert the model to a dictionary structure."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp,
            "solved": self.solved,
            "has_fix": self.has_fix,
            "audit_id": str(self.audit_id),
        }


class Audit(SQLModel, table=True):
    """
    Represents an audit record for the routing of an Exception.
    """

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for the audit record.",
        primary_key=True,
    )
    timestamp: str = Field(
        datetime.now(),
        description="Timestamp of when the exception record was created.",
    )
    reasoning: str = Field(
        ..., description="The reasoning behind the routing decision."
    )
    module_id: uuid.UUID = Field(
        ...,
        description="ID of the module that handled the exception.",
        foreign_key="module.id",
    )
    exception_id: uuid.UUID = Field(
        ...,
        foreign_key="robotexception.id",
        description="ID of the exception that was routed for resolution.",
    )

    def to_json(self) -> dict:
        """Convert the model to a dictionary structure."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp,
            "reasoning": self.reasoning,
            "module_id": str(self.module_id),
            "exception_id": str(self.exception_id),
        }
