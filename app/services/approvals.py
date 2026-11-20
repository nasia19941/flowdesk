from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Request, RequestAction, User, WorkflowStep
from app.models.enums import Decision, RequestStatus


def get_current_step(request: Request) -> WorkflowStep | None:
    for step in request.workflow.steps:
        if step.step_order == request.current_step_order:
            return step
    return None


def decide(
    request: Request,
    user: User,
    decision: Decision,
    comment: str | None,
    db: Session,
) -> Request:
    if request.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only pending requests can be decided (current status: {request.status.value})",
        )
    if request.requester_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot decide on your own request",
        )

    step = get_current_step(request)
    if step is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The current step of this request no longer exists",
        )
    if step.approver_role != user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This step needs a {step.approver_role.value} approver",
        )

    db.add(
        RequestAction(
            request_id=request.id,
            actor_id=user.id,
            step_order=step.step_order,
            decision=decision,
            comment=comment,
        )
    )

    last_step_order = request.workflow.steps[-1].step_order
    if decision == Decision.REJECTED:
        request.status = RequestStatus.REJECTED
        request.current_step_order = None
    elif step.step_order == last_step_order:
        request.status = RequestStatus.APPROVED
        request.current_step_order = None
    else:
        request.current_step_order = step.step_order + 1

    db.commit()
    db.refresh(request)
    return request