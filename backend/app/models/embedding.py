from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.models.base import Base


settings = get_settings()


class Embedding(Base):
    __tablename__ = "embeddings"

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), primary_key=True, index=True)
    embedding_vector: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    job = relationship("Job", back_populates="embedding")
