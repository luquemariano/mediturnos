from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.consultorio import Consultorio
    from app.models.usuario import Usuario


class ConsultorioAdministrador(Base):
    """Autoridad administrativa del consultorio, independiente de CuentaUsuario."""

    __tablename__ = "consultorio_administradores"
    __table_args__ = (
        UniqueConstraint("consultorio_id", "usuario_id", name="uq_consultorio_administradores_usuario"),
        CheckConstraint("rol IN ('propietaria', 'administradora')", name="ck_consultorio_administradores_rol"),
        Index(
            "uq_consultorio_administradores_propietaria",
            "consultorio_id",
            unique=True,
            sqlite_where=text("rol = 'propietaria'"),
            postgresql_where=text("rol = 'propietaria'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(
        ForeignKey("consultorios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)

    consultorio: Mapped["Consultorio"] = relationship(back_populates="administradores")
    usuario: Mapped["Usuario"] = relationship()
