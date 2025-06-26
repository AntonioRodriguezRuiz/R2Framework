# This file defines the different modules that can be used in the database.

from sqlmodel import Session, select
from gateway.models import Module
from gateway.enums import ExceptionType


def populate_modules(engine):
    """
    Populates the database with the default modules for the R2Framework.
    This includes:
    - UI Error Module: Handles UI-related exceptions with screenshot access
    - General Error Module: Handles all other types of exceptions
    """

    with Session(engine) as session:
        existing_modules = session.exec(select(Module)).unique()
        if existing_modules:
            print("Modules already populated. Skipping population.")
            return

        ui_error_module = Module(
            name="UI Error Handler",
            description=(
                """
                ## Module description
                Module responsible for managing UI-related errors.
                This module has access to the current UI state via screenshots and is provided with visual information about the moment where execution failed.
                It specializes in identifying and resolving issues related to user interface interactions, element detection, and visual validation failures.

                ## Module restrictions
                - Must have access to current UI via screenshots
                - Must be provided visual information about execution failure moment

                ## Example error types
                - Error raised when a UI element cannot be located
                """
            ),
            enabled=True,
            routing_tool="ui_exception_handler",
        )

        # General Error Module
        general_error_module = Module(
            name="General Error Handler",
            description=(
                """
                ## Module description
                Module responsible for managing all non-UI related errors.
                This module handles system exceptions, robot exceptions, user exceptions,
                and any other error types that don't require visual interface access.
                It focuses on logical errors, system failures, data processing issues,
                and general application exceptions.

                ## Module restrictions
                - Cannot process visual information

                ## Example error types
                - Error raised when a system resource is unavailable
                - Error raised when a robot encounters a logical failure
                """
            ),
            enabled=True,
            routing_tool="route_general_error",
        )

        # Add modules to session
        session.add(ui_error_module)
        session.add(general_error_module)
        session.commit()

        print(f"Successfully populated modules")
