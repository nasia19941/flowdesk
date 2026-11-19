from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Request, User, Workflow, WorkflowStep
from app.models.enums import Role
from app.schemas.workflow import WorkflowIn, WorkflowRead

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_workflow_or_404(workflow_id: int, db: Session) -> Workflow:
    workflow = db.get(Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


def ensure_name_is_free(name: str, db: Session, exclude_id: int | None = None) -> None:
    query = select(Workflow).where(Workflow.name == name)
    if exclude_id is not None:
        query = query.where(Workflow.id != exclude_id)
    if db.scalar(query):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A workflow with this name already exists",
        )


def build_steps(data: WorkflowIn) -> list[WorkflowStep]:
    return [
        WorkflowStep(step_order=index, name=step.name, approver_role=step.approver_role)
        for index, step in enumerate(data.steps, start=1)
    ]


@router.post("", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def create_workflow(
    data: WorkflowIn,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(Role.ADMIN)),
):
    ensure_name_is_free(data.name, db)

    workflow = Workflow(name=data.name, description=data.description, steps=build_steps(data))
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


@router.get("", response_model=list[WorkflowRead])
def list_workflows(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.scalars(select(Workflow).order_by(Workflow.id)).all()


@router.get("/{workflow_id}", response_model=WorkflowRead)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return get_workflow_or_404(workflow_id, db)


@router.put("/{workflow_id}", response_model=WorkflowRead)
def replace_workflow(
    workflow_id: int,
    data: WorkflowIn,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(Role.ADMIN)),
):
    workflow = get_workflow_or_404(workflow_id, db)
    ensure_name_is_free(data.name, db, exclude_id=workflow_id)

    workflow.name = data.name
    workflow.description = data.description
    workflow.steps.clear()
    db.flush()
    workflow.steps.extend(build_steps(data))

    db.commit()
    db.refresh(workflow)
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(Role.ADMIN)),
):
    workflow = get_workflow_or_404(workflow_id, db)

    requests_count = db.scalar(
        select(func.count()).select_from(Request).where(Request.workflow_id == workflow_id)
    )
    if requests_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This workflow has requests and cannot be deleted",
        )

    db.delete(workflow)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)