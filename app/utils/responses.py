from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper for all endpoints."""

    success: bool
    message: str
    data: Optional[T] = None
    error_code: Optional[str] = None

    class Config:
        json_encoders = {
            # Handle datetime serialization if needed
        }


def success_response(
    message: str = "Operation successful",
    data: Optional[Any] = None,
) -> dict:
    """Create a standard success response."""
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error_response(
    message: str = "An error occurred",
    error_code: str = "INTERNAL_ERROR",
) -> dict:
    """Create a standard error response."""
    return {
        "success": False,
        "message": message,
        "error_code": error_code,
    }
