from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Source(Base, TimestampMixin):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_sources_user_url"),
        Index("ix_sources_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    refresh_interval: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    custom_selectors: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="sources")
    jobs = relationship("Job", back_populates="source", cascade="all, delete-orphan")
    extraction_logs = relationship(
        "ExtractionLog", back_populates="source", cascade="all, delete-orphan"
    )
