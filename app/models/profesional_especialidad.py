from sqlalchemy import Column, ForeignKey, Integer, Table

from app.database.connection import Base


profesionales_especialidades = Table(
    "profesionales_especialidades",
    Base.metadata,
    Column(
        "profesional_id",
        Integer,
        ForeignKey("profesionales.id"),
        primary_key=True,
    ),
    Column(
        "especialidad_id",
        Integer,
        ForeignKey("especialidades.id"),
        primary_key=True,
    ),
)