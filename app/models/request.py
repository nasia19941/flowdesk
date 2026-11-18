from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import Decision, RequestStatus


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus), default=RequestStatus.DRAFT, index=True
    )
    current_step_order: Mapped[int | None]

    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"))
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    workflow: Mapped["Workflow"] = relationship()
    requester: Mapped["User"] = relationship(back_populates="requests")
    actions: Mapped[list["RequestAction"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class RequestAction(Base):
    __tablename__ = "request_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"))
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    step_order: Mapped[int]
    decision: Mapped[Decision] = mapped_column(Enum(Decision))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    request: Mapped["Request"] = relationship(back_populates="actions")
    actor: Mapped["User"] = relationship()