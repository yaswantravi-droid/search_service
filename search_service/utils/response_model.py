from typing import Optional
from pydantic import BaseModel, Field


class IResponseModel(BaseModel):
    """Base response model for all API responses."""
    message: Optional[str] = Field(
        default=None,
        description="A message providing additional context about the response.",
    )
