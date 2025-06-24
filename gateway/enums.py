# Declares the enums used in the gateway module models

from enum import Enum

class ExceptionType(str, Enum):
    """
    Enum representing the type of exception.
    TODO: Set types of exception according to amrojas paper
    """
    ROBOT_EXCEPTION = "robot_exception"
    SYSTEM_EXCEPTION = "system_exception"
    USER_EXCEPTION = "user_exception"
    UI_EXCEPTION = "ui_exception"