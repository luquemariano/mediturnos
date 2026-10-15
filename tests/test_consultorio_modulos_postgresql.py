"""Concurrency and GiST exclusion checks against a real PostgreSQL database."""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, time, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker

from app.models.consultorio import Consultorio
from app.models.consultorio_administrador import ConsultorioAdministrador
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.cuenta import Cuenta
from app.models.ocurrencia_modulo import OcurrenciaModulo
from app.models.regla_recurrencia_modulo import ReglaRecurrenciaModulo
from app.models.profesional import Profesional
from app.models.sala import Sala
from app.models.usuario import Usuario
from app.repositories.consultorio_modulo_repository import listar_mis_ocurrencias_activas
from app.schemas.consultorio_modulo import ReglaModuloCrear
from app.services.consultorio_modulo_service import _crear_ocurrencias_regla, crear_regla


POSTGRES_URL = os.getenv("TEST_POSTGRES_CONSULTORIO_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="Requiere PostgreSQL real mediante TEST_POSTGRES_CONSULTORIO_URL.")


def _escenario():
    engine = create_engine(POSTGRES_URL, pool_size=8, max_overflow=4)
    Sessions = sessionmaker(bind=engine, expire_on_commit=False)
    key = uuid4().hex
    with Sessions() as db:
        individual = Cuenta(nombre=f"Individual {key}", tipo="individual")
        organizacion = Cuenta(nombre=f"Organización {key}", tipo="organizacion")
        user = Usuario(nombre="Titular sintética", email=f"titular-{key}@consultorio.test", password_hash="test-only", rol="profesional")
        db.add_all([individual, organizacion, user]); db.flush()
        professional = Profesional(usuario_id=user.id, cuenta_id=individual.id, nombre="Profesional", apellido="Sintético", matricula=f"PG-{key[:10]}")
        clinic = Consultorio(cuenta_id=organizacion.id, nombre=f"Consultorio {key}")
        db.add_all([professional, clinic]); db.flush()
        room = Sala(consultorio_id=clinic.id, nombre="Sala", codigo=key[:30])
        db.add_all([room, ConsultorioAdministrador(consultorio_id=clinic.id, usuario_id=user.id, rol="propietaria")]); db.flush()
        db.add(ConsultorioProfesional(consultorio_id=clinic.id, profesional_id=professional.id, estado="activo"))
        db.commit()
        ids = (user.id, professional.id, clinic.id, room.id, individual.id, organizacion.id)
    return engine, Sessions, key, ids


def _limpiar(engine, ids):
    user_id, professional_id, clinic_id, room_id, individual_id, organization_id = ids
    from sqlalchemy import text
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM consultorio_solicitudes_cambio_modulo WHERE consultorio_id=:id"), {"id": clinic_id})
        connection.execute(text("DELETE FROM consultorio_ocurrencias_modulo WHERE consultorio_id=:id"), {"id": clinic_id})
        connection.execute(text("DELETE FROM consultorio_reglas_modulo WHERE serie_id IN (SELECT id FROM consultorio_series_modulo WHERE consultorio_id=:id)"), {"id": clinic_id})
        connection.execute(text("DELETE FROM consultorio_series_modulo WHERE consultorio_id=:id"), {"id": clinic_id})
        connection.execute(text("DELETE FROM consultorio_profesionales WHERE consultorio_id=:id"), {"id": clinic_id})
        connection.execute(text("DELETE FROM consultorio_administradores WHERE consultorio_id=:id"), {"id": clinic_id})
        connection.execute(text("DELETE FROM consultorio_salas WHERE id=:id"), {"id": room_id})
        connection.execute(text("DELETE FROM consultorios WHERE id=:id"), {"id": clinic_id})
        connection.execute(text("DELETE FROM profesionales WHERE id=:id"), {"id": professional_id})
        connection.execute(text("DELETE FROM usuarios WHERE id=:id"), {"id": user_id})
        connection.execute(text("DELETE FROM cuentas WHERE id IN (:a,:b)"), {"a": individual_id, "b": organization_id})


def test_exclusion_gist_serializa_modulos_solapados_y_acepta_adyacentes():
    engine, Sessions, key, ids = _escenario()
    user_id, professional_id, clinic_id, room_id, *_ = ids
    inicio = datetime.now(UTC) + timedelta(days=35)
    fin = inicio + timedelta(hours=4)
    barrier = Barrier(2)

    def insertar():
        with Sessions() as db:
            barrier.wait(timeout=10)
            db.add(OcurrenciaModulo(consultorio_id=clinic_id, sala_id=room_id, profesional_id=professional_id, fecha_inicio=inicio, fecha_fin=fin, estado="activa", origen="extraordinaria", creado_por_usuario_id=user_id))
            try:
                db.commit()
                return "created"
            except IntegrityError as error:
                db.rollback()
                assert getattr(error.orig, "sqlstate", None) == "23P01"
                return "rejected"
            except OperationalError as error:
                db.rollback()
                # PostgreSQL may abort one simultaneous GiST check as a deadlock;
                # the room-row lock in application services avoids this path.
                assert getattr(error.orig, "sqlstate", None) == "40P01"
                return "rejected"

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: insertar(), range(2)))
        assert sorted(results) == ["created", "rejected"]
        with Sessions() as db:
            first = db.query(OcurrenciaModulo).filter_by(consultorio_id=clinic_id).one()
            overlapping = OcurrenciaModulo(consultorio_id=clinic_id, sala_id=room_id, profesional_id=professional_id, fecha_inicio=first.fecha_inicio + timedelta(minutes=15), fecha_fin=first.fecha_fin + timedelta(minutes=15), estado="activa", origen="extraordinaria", creado_por_usuario_id=user_id)
            db.add(overlapping)
            with pytest.raises(IntegrityError) as conflict:
                db.commit()
            db.rollback()
            assert getattr(conflict.value.orig, "sqlstate", None) == "23P01"
            adjacent = OcurrenciaModulo(consultorio_id=clinic_id, sala_id=room_id, profesional_id=professional_id, fecha_inicio=first.fecha_fin, fecha_fin=first.fecha_fin + timedelta(hours=4), estado="activa", origen="extraordinaria", creado_por_usuario_id=user_id)
            db.add(adjacent); db.commit()
            assert db.query(OcurrenciaModulo).filter_by(consultorio_id=clinic_id).count() == 2
    finally:
        _limpiar(engine, ids)
        engine.dispose()


def test_lock_de_sala_rechaza_reglas_semanales_concurrentes():
    engine, Sessions, key, ids = _escenario()
    user_id, _, clinic_id, room_id, *_ = ids
    barrier = Barrier(2)
    hoy = date.today() + timedelta(days=120)
    dia = hoy.weekday()

    def crear(hora):
        with Sessions() as db:
            user = db.get(Usuario, user_id)
            barrier.wait(timeout=10)
            payload = ReglaModuloCrear(sala_id=room_id, profesional_id=ids[1], dia_semana=dia, hora_inicio=hora, vigente_desde=hoy)
            try:
                crear_regla(db, user, clinic_id, payload)
                return "created"
            except HTTPException as error:
                db.rollback()
                assert error.status_code == 409
                return "rejected"

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(crear, (time(9), time(10))))
        assert sorted(results) == ["created", "rejected"]
    finally:
        _limpiar(engine, ids)
        engine.dispose()


def test_dos_generadores_concurrentes_materializan_una_vez_por_fecha_civil():
    engine, Sessions, key, ids = _escenario()
    user_id, professional_id, clinic_id, room_id, *_ = ids
    fecha_inicio = date.today() + timedelta(days=120)
    dia = fecha_inicio.weekday()
    with Sessions() as db:
        user = db.get(Usuario, user_id)
        regla = crear_regla(db, user, clinic_id, ReglaModuloCrear(
            sala_id=room_id,
            profesional_id=professional_id,
            dia_semana=dia,
            hora_inicio=time(9),
            vigente_desde=fecha_inicio,
        ))
        regla_id = regla.id
    barrier = Barrier(2)

    def expandir():
        with Sessions() as db:
            consultorio = db.get(Consultorio, clinic_id)
            regla = db.get(ReglaRecurrenciaModulo, regla_id)
            barrier.wait(timeout=10)
            creadas = _crear_ocurrencias_regla(
                db,
                consultorio,
                regla,
                date.today(),
                date.today() + timedelta(days=150),
                user_id,
            )
            db.commit()
            return creadas

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: expandir(), range(2)))
        with Sessions() as db:
            count = db.query(OcurrenciaModulo).filter_by(regla_id=regla_id).count()
        assert sum(results) == count
        assert count >= 4
    finally:
        _limpiar(engine, ids)
        engine.dispose()


def test_consulta_postgresql_filtra_modulos_por_cuenta_y_vinculo():
    engine, Sessions, key, ids = _escenario()
    user_a_id, professional_a_id, clinic_id, room_id, *_ = ids
    user_b_id = professional_b_id = account_b_id = None
    try:
        with Sessions() as db:
            account_b = Cuenta(nombre=f"Individual B {key}", tipo="individual")
            user_b = Usuario(nombre="Profesional B", email=f"profesional-b-{key}@consultorio.test", password_hash="test-only", rol="profesional")
            db.add_all([account_b, user_b]); db.flush()
            professional_b = Profesional(usuario_id=user_b.id, cuenta_id=account_b.id, nombre="Profesional", apellido="B", matricula=f"PGB-{key[:10]}")
            db.add(professional_b); db.flush()
            db.add(ConsultorioProfesional(consultorio_id=clinic_id, profesional_id=professional_b.id, estado="preparatorio"))
            inicio = datetime.now(UTC) + timedelta(days=12)
            a = OcurrenciaModulo(consultorio_id=clinic_id, sala_id=room_id, profesional_id=professional_a_id, fecha_inicio=inicio, fecha_fin=inicio + timedelta(hours=4), estado="activa", origen="extraordinaria")
            b = OcurrenciaModulo(consultorio_id=clinic_id, sala_id=room_id, profesional_id=professional_b.id, fecha_inicio=inicio + timedelta(hours=5), fecha_fin=inicio + timedelta(hours=9), estado="activa", origen="extraordinaria")
            b_suspendida = OcurrenciaModulo(consultorio_id=clinic_id, sala_id=room_id, profesional_id=professional_b.id, fecha_inicio=inicio + timedelta(hours=10), fecha_fin=inicio + timedelta(hours=14), estado="suspendida", origen="extraordinaria")
            db.add_all([a, b, b_suspendida]); db.commit()
            user_b_id, professional_b_id, account_b_id = user_b.id, professional_b.id, account_b.id
            resultados_a = listar_mis_ocurrencias_activas(db, user_a_id, datetime.now(UTC))
            resultados_b = listar_mis_ocurrencias_activas(db, user_b_id, datetime.now(UTC))
            assert [item.profesional_id for item in resultados_a] == [professional_a_id]
            assert [item.profesional_id for item in resultados_b] == [professional_b_id]
            assert [item.estado for item in resultados_b] == ["activa"]
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM consultorio_ocurrencias_modulo WHERE consultorio_id=:id"), {"id": clinic_id})
            connection.execute(text("DELETE FROM consultorio_profesionales WHERE profesional_id=:id"), {"id": professional_b_id}) if professional_b_id else None
            connection.execute(text("DELETE FROM profesionales WHERE id=:id"), {"id": professional_b_id}) if professional_b_id else None
            connection.execute(text("DELETE FROM usuarios WHERE id=:id"), {"id": user_b_id}) if user_b_id else None
            connection.execute(text("DELETE FROM cuentas WHERE id=:id"), {"id": account_b_id}) if account_b_id else None
        _limpiar(engine, ids)
        engine.dispose()
