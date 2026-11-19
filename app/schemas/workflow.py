from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import Role


class WorkflowStepIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    approver_role: Role

    @field_validator("approver_role")
    @classmethod
    def approver_cannot_be_employee(cls, value: Role) -> Role:
        if value == Role.EMPLOYEE:
            raise ValueError("An approval step cannot be assigned to employees")
        return value


class WorkflowIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    steps: list[WorkflowStepIn] = Field(min_length=1, max_length=10)


class WorkflowStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    step_order: int
    name: str
    approver_role: Role


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime
    steps: list[WorkflowStepRead]