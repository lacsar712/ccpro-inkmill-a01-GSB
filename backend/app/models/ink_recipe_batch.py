from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

BATCH_STATUSES = ("draft", "mixing", "qc_pass", "scrap")
BATCH_TERMINAL_STATUSES = ("qc_pass", "scrap")

# 合法状态流转：draft -> mixing -> qc_pass | scrap
BATCH_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "draft": ("mixing",),
    "mixing": ("qc_pass", "scrap"),
    "qc_pass": (),
    "scrap": (),
}

BATCH_STATUS_LABELS = {
    "draft": "草稿",
    "mixing": "调合中",
    "qc_pass": "QC 合格",
    "scrap": "报废",
}


class InkRecipeBatch(Base):
    """色浆配方批次（挂车间，非通用配方/电商实体）。"""

    __tablename__ = "ink_recipe_batches"
    __table_args__ = (
        UniqueConstraint("workshop_id", "batch_code", name="uq_batch_workshop_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workshop_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workshops.id", ondelete="CASCADE"), nullable=False
    )
    batch_code: Mapped[str] = mapped_column(String(64), nullable=False)
    pigment_base: Mapped[str] = mapped_column(String(128), nullable=False)
    target_viscosity_pa_s: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    workshop: Mapped["Workshop"] = relationship("Workshop", back_populates="recipe_batches")
