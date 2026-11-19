from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Request, User, Workflow
from app.models.enums import RequestStatus, Role
from app.schemas.request import RequestCreate, RequestRead

router = APIRouter(prefix="/requests", tags=["requests"])


def get_request_or_404(request_id: int, db: Session) -> Request:
    request = db.get(Request, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return request


def ensure_can_view(request: Request, user: User) -> None:
    if request.requester_id != user.id and user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this request",
        )


@router.post("", response_model=RequestRead, status_code=status.HTTP_201_CREATED)
def create_request(
    data: RequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.get(Workflow, data.workflow_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    request = Request(
        title=data.title,
        description=data.description,
        amount=data.amount,
        workflow_id=data.workflow_id,
        requester_id=current_user.id,
        status=RequestStatus.DRAFT,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.get("/mine", response_model=list[RequestRead])
def list_my_requests(
    status_filter: RequestStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Request).where(Request.requester_id == current_user.id)
    if status_filter is not None:
        query = query.where(Request.status == status_filter)
    return db.scalars(query.order_by(Request.created_at.desc())).all()


@router.get("/{request_id}", response_model=RequestRead)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = get_request_or_404(request_id, db)
    ensure_can_view(request, current_user)
    return request


@router.post("/{request_id}/submit", response_model=RequestRead)
def submit_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = get_request_or_404(request_id, db)

    if request.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requester can submit this request",
        )
    if request.status != RequestStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only draft requests can be submitted (current status: {request.status.value})",
        )

    request.status = RequestStatus.PENDING
    request.current_step_order = 1
    db.commit()
    db.refresh(request)
    return request