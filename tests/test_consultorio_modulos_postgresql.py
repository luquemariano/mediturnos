"""Concurrency and GiST exclusion checks against a real PostgreSQL database."""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, time, timedelta
import secrets
from threading import Barrier
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker

from app.models.consultorio import Consultorio
from app.models.consultorio_administrador import ConsultorioAdministrador
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.invitacion_consultorio import InvitacionConsultorio
from app.models.cuenta import Cuenta
from app.models.ocurrencia_modulo import OcurrenciaModulo
from app.models.regla_recurrencia_modulo import ReglaRecurrenciaModulo
from app.models.profesional import Profesional
from app.models.sala import Sala
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.especialidad import Especialidad
from app.models.prestacion import Prestacion
from app.models.turno import Turno
from app.repositories.consultorio_modulo_repository import listar_mis_ocurrencias_activas
from app.schemas.consultorio_modulo import ReglaModuloCrear, ModuloOcurrenciaActualizar, ModuloExtraordinarioCrear
from app.schemas.consultorio_invitacion import InvitacionCrear
from app.services.consultorio_invitacion_service import crear_invitacion
from app.services.consultorio_modulo_service import _crear_ocurrencias_regla, crear_regla, suspender_ocurrencia, actualizar_ocurrencia, crear_modulo_extraordinario, listar_modulos


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
        connection.execute(text("DELETE FROM consultorio_invitaciones WHERE consultorio_id=:id"), {"id": clinic_id})
        connection.execute(text("DELETE FROM consultorio_profesionales WHERE consultorio_id=:id"), {"id": clinic_id})
        connection.execute(text("DELETE FROM consultorio_administradores WHERE consultorio_id=:id"), {"id": clinic_id})
        connection.execute(text("DELETE FROM consultorio_salas WHERE id=:id"), {"id": room_id})
        connection.execute(text("DELETE FROM consultorios WHERE id=:id"), {"id": clinic_id})
        connection.execute(text("DELETE FROM profesionales WHERE id=:id"), {"id": professional_id})
        connection.execute(text("DELETE FROM usuarios WHERE id=:id"), {"id": user_id})
        connection.execute(text("DELETE FROM cuentas WHERE id IN (:a,:b)"), {"a": individual_id, "b": organization_id})


def _escenario_invitacion():
    engine, Sessions, key, ids = _escenario()
    from app.services.consultorio_invitacion_service import _hash
    owner_id, _, clinic_id, _, *_ = ids
    with Sessions() as db:
        account = Cuenta(nombre=f"Invitada {key}", tipo="individual")
        invited_user = Usuario(nombre="Invitada sintética", email=f"invitee-{key}@example.com", password_hash="test-only", rol="profesional", email_verificado=True)
        db.add_all([account, invited_user]); db.flush()
        invited_professional = Profesional(usuario_id=invited_user.id, cuenta_id=account.id, nombre="Invitada", apellido="Sintética", matricula=f"INV-{key[:10]}", email=invited_user.email)
        db.add(invited_professional); db.flush()
        token = secrets.token_urlsafe(32)
        invitation = InvitacionConsultorio(consultorio_id=clinic_id, email_normalizado=invited_user.email, estado="pendiente", token_hash=_hash(token), invitante_usuario_id=owner_id, vence_en=datetime.now(UTC) + timedelta(days=2))
        db.add(invitation); db.commit()
        values = (invited_user.id, invited_professional.id, account.id, invitation.id, token)
    return engine, Sessions, key, ids, values


def _limpiar_escenario_invitacion(engine, ids, values):
    _, _, clinic_id, *_ = ids
    invited_user_id, professional_id, account_id, invitation_id, _ = values
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM consultorio_invitaciones WHERE id=:id"), {"id": invitation_id})
        connection.execute(text("DELETE FROM consultorio_profesionales WHERE consultorio_id=:clinic AND profesional_id=:professional"), {"clinic": clinic_id, "professional": professional_id})
        connection.execute(text("DELETE FROM profesionales WHERE id=:id"), {"id": professional_id})
        connection.execute(text("DELETE FROM usuarios WHERE id=:id"), {"id": invited_user_id})
        connection.execute(text("DELETE FROM cuentas WHERE id=:id"), {"id": account_id})
    _limpiar(engine, ids)


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


def test_cupo_de_invitaciones_se_serializa_bajo_concurrencia_postgresql():
    from app.schemas.consultorio_invitacion import InvitacionCrear
    from app.services.consultorio_invitacion_service import crear_invitacion
    engine, Sessions, key, ids = _escenario()
    user_id, _, clinic_id, room_id, *_ = ids
    with Sessions() as db:
        db.get(Consultorio, clinic_id).cupo_profesionales = 2
        db.commit()
    barrier = Barrier(2)
    start = date.today() + timedelta(days=120)

    def reserve(index):
        with Sessions() as db:
            user = db.get(Usuario, user_id)
            payload = InvitacionCrear(email=f"pending-{index}-{key}@example.com", modulos=[{"sala_id": room_id, "dia_semana": start.weekday(), "hora_inicio": "09:00", "vigente_desde": start}])
            barrier.wait(timeout=10)
            try:
                crear_invitacion(db, user, clinic_id, payload)
                return "created"
            except HTTPException as exc:
                db.rollback()
                assert exc.status_code == 409
                return f"rejected:{exc.detail}"

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            outcomes = sorted(workers.map(reserve, (1, 2)))
        assert sum(item == "created" for item in outcomes) == 1, outcomes
        assert sum(item.startswith("rejected:") for item in outcomes) == 1, outcomes
        with Sessions() as db:
            assert db.query(InvitacionConsultorio).filter_by(consultorio_id=clinic_id, estado="preparacion").count() == 1
    finally:
        _limpiar(engine, ids)
        engine.dispose()


def test_exclusion_gist_cubre_reserva_pendiente_de_invitacion():
    engine, Sessions, key, ids = _escenario()
    user_id, professional_id, clinic_id, room_id, *_ = ids
    inicio = datetime.now(UTC) + timedelta(days=36)
    with Sessions() as db:
        invite = InvitacionConsultorio(consultorio_id=clinic_id, email_normalizado=f"reserved-{key}@example.com", nombre_visible="Invitado", estado="preparacion", invitante_usuario_id=user_id, vence_en=inicio + timedelta(days=7))
        db.add(invite); db.flush()
        pending = OcurrenciaModulo(consultorio_id=clinic_id, sala_id=room_id, profesional_id=None, invitacion_id=invite.id, fecha_inicio=inicio, fecha_fin=inicio + timedelta(hours=4), estado="activa", origen="extraordinaria", creado_por_usuario_id=user_id)
        db.add(pending); db.commit()
        conflicting = OcurrenciaModulo(consultorio_id=clinic_id, sala_id=room_id, profesional_id=professional_id, fecha_inicio=inicio + timedelta(minutes=15), fecha_fin=inicio + timedelta(hours=4, minutes=15), estado="activa", origen="extraordinaria", creado_por_usuario_id=user_id)
        db.add(conflicting)
        with pytest.raises(IntegrityError) as conflict:
            db.commit()
        db.rollback()
        assert getattr(conflict.value.orig, "sqlstate", None) == "23P01"
    try:
        pass
    finally:
        _limpiar(engine, ids)
        engine.dispose()


def test_aceptacion_concurrente_es_idempotente_en_postgresql():
    from app.services.consultorio_invitacion_service import aceptar_invitacion
    engine, Sessions, _, ids, values = _escenario_invitacion()
    invited_user_id, professional_id, _, invite_id, token = values
    barrier = Barrier(2)

    def accept():
        with Sessions() as db:
            user = db.get(Usuario, invited_user_id)
            barrier.wait(timeout=10)
            try:
                result = aceptar_invitacion(db, user, token)
                return result["mensaje"]
            except HTTPException as exc:
                db.rollback()
                return f"rejected:{exc.status_code}"

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            outcomes = list(workers.map(lambda _: accept(), range(2)))
        assert outcomes.count("Invitación aceptada.") == 1
        assert outcomes.count("La invitación ya fue aceptada.") == 1
        with Sessions() as db:
            assert db.query(ConsultorioProfesional).filter_by(consultorio_id=ids[2], profesional_id=professional_id, estado="activo").count() == 1
            assert db.get(InvitacionConsultorio, invite_id).estado == "aceptada"
    finally:
        _limpiar_escenario_invitacion(engine, ids, values)
        engine.dispose()


def test_revocacion_y_aceptacion_concurrentes_se_serializan_en_postgresql():
    from app.services.consultorio_invitacion_service import aceptar_invitacion, revocar_invitacion
    engine, Sessions, _, ids, values = _escenario_invitacion()
    owner_id, _, clinic_id, _, *_ = ids
    invited_user_id, _, _, invite_id, token = values
    barrier = Barrier(2)

    def accept():
        with Sessions() as db:
            user = db.get(Usuario, invited_user_id)
            barrier.wait(timeout=10)
            try:
                aceptar_invitacion(db, user, token)
                return "accepted"
            except HTTPException as exc:
                db.rollback()
                assert exc.status_code == 400
                return "rejected"

    def revoke():
        with Sessions() as db:
            user = db.get(Usuario, owner_id)
            barrier.wait(timeout=10)
            try:
                revocar_invitacion(db, user, clinic_id, invite_id)
                return "revoked"
            except HTTPException as exc:
                db.rollback()
                assert exc.status_code == 409
                return "rejected"

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(accept), workers.submit(revoke)]
            outcomes = [future.result() for future in futures]
        assert outcomes.count("accepted") + outcomes.count("revoked") == 1
        assert outcomes.count("rejected") == 1
        with Sessions() as db:
            state = db.get(InvitacionConsultorio, invite_id).estado
            assert state == ("aceptada" if "accepted" in outcomes else "revocada")
    finally:
        _limpiar_escenario_invitacion(engine, ids, values)
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


def test_postgresql_bloquea_modulo_con_turno_y_permite_cambio_de_modulo_libre():
    engine, Sessions, key, ids = _escenario()
    user_id, professional_id, clinic_id, room_id, *_ = ids
    turno_id = patient_id = specialty_id = prestation_id = None
    try:
        with Sessions() as db:
            patient = Paciente(nombre="Paciente QA sintético", apellido="No real", activo=True)
            specialty = Especialidad(nombre=f"QA-{key[:12]}", activa=True)
            db.add_all((patient, specialty)); db.flush()
            prestation = Prestacion(profesional_id=professional_id, especialidad_id=specialty.id, nombre="Consulta QA", duracion_minutos=30, precio=1, activa=True)
            db.add(prestation); db.flush()
            owner = db.get(Usuario, user_id)
            occupied_start = datetime.now(UTC) + timedelta(days=35)
            occupied = OcurrenciaModulo(consultorio_id=clinic_id, sala_id=room_id, profesional_id=professional_id, fecha_inicio=occupied_start, fecha_fin=occupied_start + timedelta(hours=4), estado="activa", origen="extraordinaria", creado_por_usuario_id=user_id)
            free_start = occupied_start + timedelta(days=7)
            free = OcurrenciaModulo(consultorio_id=clinic_id, sala_id=room_id, profesional_id=professional_id, fecha_inicio=free_start, fecha_fin=free_start + timedelta(hours=4), estado="activa", origen="extraordinaria", creado_por_usuario_id=user_id)
            db.add_all((occupied, free)); db.flush()
            appointment = Turno(paciente_id=patient.id, prestacion_id=prestation.id, profesional_id=professional_id, fecha_hora=occupied_start + timedelta(hours=1), fecha_fin=occupied_start + timedelta(hours=1, minutes=30), estado="reservado")
            db.add(appointment); db.commit()
            occupied_id, free_id = occupied.id, free.id
            turno_id, patient_id, specialty_id, prestation_id = appointment.id, patient.id, specialty.id, prestation.id
            try:
                actualizar_ocurrencia(db, owner, clinic_id, occupied_id, ModuloOcurrenciaActualizar(
                    fecha_fin=occupied_start + timedelta(minutes=45),
                ))
                raise AssertionError("El cambio de franja debía bloquearse por el turno.")
            except HTTPException as error:
                assert error.status_code == 409
                assert error.detail == {"mensaje": "El cambio requiere resolver turnos comprometidos.", "turnos_afectados": 1}
            try:
                suspender_ocurrencia(db, owner, clinic_id, occupied_id)
                raise AssertionError("La suspensión debía bloquearse por el turno.")
            except HTTPException as error:
                assert error.status_code == 409
                assert error.detail == {"mensaje": "El módulo tiene turnos comprometidos.", "turnos_afectados": 1}
            moved_start = free_start + timedelta(days=1)
            updated = actualizar_ocurrencia(db, owner, clinic_id, free_id, ModuloOcurrenciaActualizar(fecha_inicio=moved_start, fecha_fin=moved_start + timedelta(hours=4)))
            assert updated.fecha_inicio == moved_start
            assert db.get(OcurrenciaModulo, occupied_id).estado == "activa"
            assert db.get(OcurrenciaModulo, free_id).estado == "activa"
    finally:
        with engine.begin() as connection:
            if turno_id: connection.execute(text("DELETE FROM turnos WHERE id=:id"), {"id": turno_id})
            if prestation_id: connection.execute(text("DELETE FROM prestaciones WHERE id=:id"), {"id": prestation_id})
            if patient_id: connection.execute(text("DELETE FROM pacientes WHERE id=:id"), {"id": patient_id})
            if specialty_id: connection.execute(text("DELETE FROM especialidades WHERE id=:id"), {"id": specialty_id})
        _limpiar(engine, ids)
        engine.dispose()


def test_postgresql_reserva_revocada_deja_de_ocupar_y_liberar_gist():
    engine, Sessions, key, ids = _escenario()
    user_id, professional_id, clinic_id, room_id, *_ = ids
    occurrence_ids = []
    try:
        zone = ZoneInfo("America/Argentina/Buenos_Aires")
        fecha = datetime.now(UTC).astimezone(zone).date() + timedelta(days=35)
        with Sessions() as db:
            user = db.get(Usuario, user_id)
            invitation = crear_invitacion(db, user, clinic_id, InvitacionCrear(
                email=f"reserva-revocable-{key}@example.com",
                modulos=[{"sala_id": room_id, "dia_semana": fecha.weekday(), "hora_inicio": "13:00", "vigente_desde": fecha}],
            ))
            invite_id = invitation["id"]
            starts = datetime.combine(fecha, time(13), tzinfo=zone).astimezone(UTC)
            visible = listar_modulos(db, user, clinic_id, starts, starts + timedelta(days=1))
            pending = [item for item in visible if item.invitacion_id == invite_id]
            assert len(pending) == 1 and pending[0].estado == "activa"
            occurrence_ids = [item.id for item in db.query(OcurrenciaModulo).filter_by(invitacion_id=invite_id).all()]

            invite_row = db.get(InvitacionConsultorio, invite_id)
            invite_row.estado = "revocada"
            invite_row.token_hash = None
            db.commit()

            after_revocation = listar_modulos(db, user, clinic_id, starts, starts + timedelta(days=1))
            assert all(item.invitacion_id != invite_id for item in after_revocation)
            assert db.get(InvitacionConsultorio, invite_id).estado == "revocada"
            assert db.query(OcurrenciaModulo).filter_by(invitacion_id=invite_id, estado="activa").count() == 0
            assert db.query(OcurrenciaModulo).filter(OcurrenciaModulo.id.in_(occurrence_ids)).filter_by(estado="cancelada").count() == len(occurrence_ids)

            released = crear_modulo_extraordinario(db, user, clinic_id, ModuloExtraordinarioCrear(
                sala_id=room_id,
                profesional_id=professional_id,
                fecha_inicio=starts,
                fecha_fin=starts + timedelta(hours=4),
            ))
            assert released.estado == "activa"
            db.commit()
    finally:
        _limpiar(engine, ids)
        engine.dispose()
