from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.study_request import StudyRequest
    from app.models.profesional import Profesional


class StudyReview(Base):
    __tablename__ = "study_reviews"
    __table_args__ = (UniqueConstraint("study_request_id", name="uq_study_reviews_request"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    study_request_id: Mapped[int] = mapped_column(ForeignKey("study_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id", ondelete="RESTRICT"), nullable=False, index=True)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    disposition: Mapped[str] = mapped_column(String(40), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    study_request: Mapped["StudyRequest"] = relationship(back_populates="review")
    profesional: Mapped["Profesional"] = relationship(back_populates="study_reviews")

    @property
    def professional_name(self) -> str:
        return f"{self.profesional.nombre} {self.profesional.apellido}".strip()
