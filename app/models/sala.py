from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.consultorio import Consultorio


class Sala(Base):
    __tablename__ = "consultorio_salas"
    __table_args__ = (
        UniqueConstraint("consultorio_id", "codigo", name="uq_consultorio_salas_codigo"),
        CheckConstraint("estado IN ('activa', 'inactiva')", name="ck_consultorio_salas_estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(
        ForeignKey("consultorios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activa", server_default="activa")

    consultorio: Mapped["Consultorio"] = relationship(back_populates="salas")
