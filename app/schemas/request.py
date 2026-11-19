from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RequestStatus


class RequestCreate(BaseModel):
    workflow_id: int
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    amount: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)


class RequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    amount: Decimal | None
    status: RequestStatus
    current_step_order: int | None
    workflow_id: int
    requester_id: int
    created_at: datetime
    updated_at: datetime