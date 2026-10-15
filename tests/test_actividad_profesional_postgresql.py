"""Checks the activity schema and conditional-matricula representation in PostgreSQL."""

import os

import pytest
from sqlalchemy import create_engine, text


POSTGRES_URL = os.getenv("TEST_POSTGRES_ACTIVIDAD_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="Requiere PostgreSQL real mediante TEST_POSTGRES_ACTIVIDAD_URL.",
)


def test_migration_crea_catalogo_reglas_y_matricula_nullable():
    engine = create_engine(POSTGRES_URL)
    try:
        with engine.connect() as connection:
            matricula_nullable = connection.execute(text(
                """SELECT is_nullable FROM information_schema.columns
                   WHERE table_name='profesionales' AND column_name='matricula'"""
            )).scalar_one()
            assert matricula_nullable == "YES"

            actividades = connection.execute(text(
                """SELECT a.codigo, a.requiere_matricula, a.requiere_especialidad,
                          e.nombre
                   FROM actividades_profesionales a
                   LEFT JOIN especialidades e ON e.id=a.especialidad_predeterminada_id
                   WHERE a.activa ORDER BY a.codigo"""
            )).all()
            reglas = {item.codigo: item for item in actividades}
            assert reglas["profesional_matriculable"].requiere_matricula is True
            assert reglas["profesional_matriculable"].requiere_especialidad is True
            assert reglas["servicios_estetica"].requiere_matricula is False
            assert reglas["servicios_estetica"].requiere_especialidad is False
            assert reglas["servicios_estetica"].nombre == "Estética"

            fk_count = connection.execute(text(
                """SELECT count(*) FROM pg_constraint
                   WHERE conname='fk_profesionales_actividad_id'"""
            )).scalar_one()
            assert fk_count == 1
    finally:
        engine.dispose()
