"""incorporar catalogo formal de 36 especialidades

Revision ID: c4a8f2e91b70
Revises: b7e2c4d91a60
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a8f2e91b70"
down_revision: Union[str, None] = "b7e2c4d91a60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CATALOGO = (
    (
        "Cardiología",
        "Prevención, diagnóstico y seguimiento de enfermedades cardiovasculares.",
        30,
    ),
    ("Cirugía General", "Atención profesional en cirugía general.", 30),
    (
        "Clínica Médica",
        "Atención integral de pacientes adultos, controles y consultas generales.",
        30,
    ),
    ("Dermatología", "Atención profesional en dermatología.", 30),
    ("Endocrinología", "Atención profesional en endocrinología.", 30),
    ("Enfermería", "Atención profesional en enfermería.", 30),
    ("Estética", "Atención profesional en estética.", 30),
    ("Fisioterapia", "Atención profesional en fisioterapia.", 30),
    ("Fonoaudiología", "Atención profesional en fonoaudiología.", 30),
    ("Gastroenterología", "Atención profesional en gastroenterología.", 30),
    ("Ginecología", "Atención profesional en ginecología.", 30),
    ("Hematología", "Atención profesional en hematología.", 30),
    ("Infectología", "Atención profesional en infectología.", 30),
    ("Kinesiología", "Atención profesional en kinesiología.", 30),
    ("Medicina Familiar", "Atención profesional en medicina familiar.", 30),
    ("Medicina General", "Atención profesional en medicina general.", 30),
    ("Medicina Laboral", "Atención profesional en medicina laboral.", 30),
    ("Medicina del Deporte", "Atención profesional en medicina del deporte.", 30),
    ("Nefrología", "Atención profesional en nefrología.", 30),
    ("Neumonología", "Atención profesional en neumonología.", 30),
    ("Neurología", "Atención profesional en neurología.", 30),
    ("Nutrición", "Atención profesional en nutrición.", 30),
    (
        "Obstetricia",
        "Atención profesional en obstetricia.",
        30,
    ),
    ("Odontología", "Atención profesional en odontología.", 30),
    ("Oftalmología", "Atención profesional en oftalmología.", 30),
    ("Oncología", "Atención profesional en oncología.", 30),
    (
        "Otorrinolaringología",
        "Atención profesional en otorrinolaringología.",
        30,
    ),
    (
        "Pediatría",
        "Atención médica integral para niños y adolescentes.",
        30,
    ),
    ("Podología", "Atención profesional en podología.", 30),
    ("Psicología", "Atención profesional en psicología.", 30),
    ("Psicopedagogía", "Atención profesional en psicopedagogía.", 30),
    (
        "Psiquiatría",
        "Evaluación, diagnóstico y tratamiento de la salud mental.",
        50,
    ),
    ("Reumatología", "Atención profesional en reumatología.", 30),
    (
        "Terapia Ocupacional",
        "Atención profesional en terapia ocupacional.",
        30,
    ),
    ("Traumatología", "Atención profesional en traumatología.", 30),
    ("Urología", "Atención profesional en urología.", 30),
)


def upgrade() -> None:
    conexion = op.get_bind()
    sentencia = sa.text(
        """
        INSERT INTO especialidades (
            nombre, descripcion, duracion_turno_minutos, activa
        )
        VALUES (:nombre, :descripcion, :duracion, TRUE)
        ON CONFLICT (nombre) DO UPDATE SET activa = TRUE
        """
    )
    for nombre, descripcion, duracion in CATALOGO:
        conexion.execute(
            sentencia,
            {
                "nombre": nombre,
                "descripcion": descripcion,
                "duracion": duracion,
            },
        )


def downgrade() -> None:
    """Conserva el catálogo para no romper relaciones creadas tras el upgrade."""
    pass
