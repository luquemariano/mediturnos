from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi import HTTPException

from app.core.datetime_utils import ahora_utc, desde_base_utc
from app.models.consultorio import Consultorio
from app.models.consultorio_administrador import ConsultorioAdministrador
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.cuenta import Cuenta
from app.models.ocurrencia_modulo import OcurrenciaModulo
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.regla_recurrencia_modulo import ReglaRecurrenciaModulo
from app.models.sala import Sala
from app.models.disponibilidad import Disponibilidad
from app.models.especialidad import Especialidad
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.serie_modulo import SerieModulo
from app.models.turno import Turno
from app.models.usuario import Usuario
from app.models.invitacion_consultorio import InvitacionConsultorio
from app.repositories import consultorio_modulo_repository
from app.services.consultorio_modulo_service import (
    _fechas_solapan_reglas,
    _instante_local_utc,
    crear_modulo_extraordinario,
    validar_turno_en_modulo,
)
from app.schemas.consultorio_modulo import ModuloExtraordinarioCrear
from app.core.dependencies import obtener_usuario_actual
from app.main import app
from tests.conftest import SessionTest
from zoneinfo import ZoneInfo


@pytest.fixture
def consultorio_modulos(client):
    db = SessionTest()
    titular = Usuario(nombre="Titular", email="titular-modulos@test.invalid", password_hash="fixture", rol="profesional")
    miembro = Usuario(nombre="Miembro", email="miembro-modulos@test.invalid", password_hash="fixture", rol="profesional")
    db.add_all([titular, miembro]); db.flush()
    profesional_titular = Profesional(usuario_id=titular.id, nombre="Valentina", apellido="Sintética", matricula="M-TEST-01")
    profesional_miembro = Profesional(usuario_id=miembro.id, nombre="Profesional", apellido="Piloto", matricula="M-TEST-02")
    cuenta = Cuenta(nombre="Consultorio modular sintético", tipo="organizacion")
    paciente = Paciente(nombre="Paciente", apellido="Sintético", activo=True)
    db.add_all([profesional_titular, profesional_miembro, cuenta, paciente]); db.flush()
    consultorio = Consultorio(cuenta_id=cuenta.id, nombre="Piloto sintético", zona_horaria="America/Argentina/Buenos_Aires", duracion_modulo_minutos=240, horizonte_materializacion_dias=90)
    sala = Sala(consultorio=consultorio, nombre="Sala piloto", codigo="PILOTO")
    db.add_all([
        consultorio,
        sala,
        ConsultorioAdministrador(consultorio=consultorio, usuario=titular, rol="propietaria"),
        ConsultorioProfesional(consultorio=consultorio, profesional=profesional_titular, estado="preparatorio"),
        ConsultorioProfesional(consultorio=consultorio, profesional=profesional_miembro, estado="activo"),
    ])
    db.commit()
    values = {"titular": titular, "miembro": miembro, "pro_a": profesional_titular, "pro_b": profesional_miembro, "consultorio": consultorio, "sala": sala, "paciente": paciente}
    yield values
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    db.close()


def _autenticar(usuario):
    app.dependency_overrides[obtener_usuario_actual] = lambda: usuario


def _agregar_ocurrencia(db, datos, profesional, inicio, *, estado="activa"):
    ocurrencia = OcurrenciaModulo(
        consultorio_id=datos["consultorio"].id,
        sala_id=datos["sala"].id,
        profesional_id=profesional.id,
        fecha_inicio=inicio,
        fecha_fin=inicio + timedelta(hours=4),
        estado=estado,
        origen="extraordinaria",
    )
    db.add(ocurrencia)
    db.flush()
    return ocurrencia


def _proxima_fecha(dia: int, *, dias_minimos: int = 1) -> date:
    hoy = ahora_utc().astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    fecha = hoy + timedelta(days=dias_minimos)
    while fecha.weekday() != dia:
        fecha += timedelta(days=1)
    return fecha


def _crear_regla(client, data, *, dia=0, hora="09:00:00", fecha=None):
    _autenticar(data["titular"])
    fecha = fecha or _proxima_fecha(dia)
    return client.post(
        f"/consultorios/{data['consultorio'].id}/reglas-modulo",
        json={"sala_id": data["sala"].id, "profesional_id": data["pro_b"].id, "dia_semana": dia, "hora_inicio": hora, "vigente_desde": fecha.isoformat()},
    )


def test_regla_semanal_materializa_90_dias_idempotente_y_respuesta_sin_pacientes(client, consultorio_modulos):
    data = consultorio_modulos
    respuesta = _crear_regla(client, data, dia=0)
    assert respuesta.status_code == 201, respuesta.text
    _autenticar(data["titular"])
    consulta = client.get(f"/consultorios/{data['consultorio'].id}/modulos")
    assert consulta.status_code == 200
    modulos = consulta.json()
    assert len(modulos) >= 12
    assert {item["profesional_id"] for item in modulos} == {data["pro_b"].id}
    assert all(item["sala_id"] == data["sala"].id for item in modulos)
    assert all(not {"paciente", "turno_id", "prestacion", "documento"} & item.keys() for item in modulos)
    cantidad = len(modulos)
    assert len(client.get(f"/consultorios/{data['consultorio'].id}/modulos").json()) == cantidad


def test_reglas_semanales_solapadas_se_rechazan_aunque_estan_fuera_del_horizonte(client, consultorio_modulos):
    data = consultorio_modulos
    desde = _proxima_fecha(2, dias_minimos=120)
    primera = _crear_regla(client, data, dia=2, hora="09:00:00", fecha=desde)
    assert primera.status_code == 201, primera.text
    segunda = client.post(
        f"/consultorios/{data['consultorio'].id}/reglas-modulo",
        json={"sala_id": data["sala"].id, "profesional_id": data["pro_b"].id, "dia_semana": 2, "hora_inicio": "12:00:00", "duracion_minutos": 240, "vigente_desde": desde.isoformat()},
    )
    assert segunda.status_code == 409
    assert "paciente" not in segunda.text.lower()
    db = SessionTest()
    assert db.query(ReglaRecurrenciaModulo).count() == 1
    db.close()


def test_solapamiento_recurrente_informa_primer_bloque_y_profesional_sin_datos_clinicos(client, consultorio_modulos):
    data = consultorio_modulos
    fecha = _proxima_fecha(0)
    existente = _crear_regla(client, data, dia=0, hora="09:00:00", fecha=fecha)
    assert existente.status_code == 201, existente.text

    conflicto = _crear_regla(client, data, dia=0, hora="10:00:00", fecha=fecha)

    assert conflicto.status_code == 409
    detalle = conflicto.json()["detail"]
    assert detalle == {
        "mensaje": "El horario de la sala ya no está disponible.",
        "fecha": fecha.isoformat(),
        "hora_inicio": "09:00",
        "hora_fin": "13:00",
        "profesional": "Profesional Piloto",
    }
    assert not {"paciente", "turno", "historia", "documento", "prestacion"} & set(detalle)


def test_modulo_extraordinario_se_suspende_y_cambio_ajeno_es_404(client, consultorio_modulos):
    data = consultorio_modulos
    _autenticar(data["titular"])
    inicio = (ahora_utc() + timedelta(days=3)).replace(minute=0, second=0, microsecond=0)
    creado = client.post(
        f"/consultorios/{data['consultorio'].id}/modulos-extraordinarios",
        json={"sala_id": data["sala"].id, "profesional_id": data["pro_b"].id, "fecha_inicio": inicio.isoformat(), "fecha_fin": (inicio + timedelta(hours=4)).isoformat()},
    )
    assert creado.status_code == 201, creado.text
    modulo_id = creado.json()["id"]
    _autenticar(data["miembro"])
    assert client.post(f"/consultorios/{data['consultorio'].id}/modulos/{modulo_id}/suspender").status_code == 404
    _autenticar(data["titular"])
    suspendido = client.post(f"/consultorios/{data['consultorio'].id}/modulos/{modulo_id}/suspender")
    assert suspendido.status_code == 200
    assert suspendido.json()["estado"] == "suspendida"


def test_suspendido_bloquea_conteo_y_no_revela_datos_de_paciente(client, consultorio_modulos):
    data = consultorio_modulos
    _autenticar(data["titular"])
    inicio = (ahora_utc() + timedelta(days=4)).replace(minute=0, second=0, microsecond=0)
    creado = client.post(
        f"/consultorios/{data['consultorio'].id}/modulos-extraordinarios",
        json={"sala_id": data["sala"].id, "profesional_id": data["pro_b"].id, "fecha_inicio": inicio.isoformat(), "fecha_fin": (inicio + timedelta(hours=4)).isoformat()},
    )
    assert creado.status_code == 201, creado.text
    db = SessionTest()
    member = db.get(Profesional, data["pro_b"].id)
    patient = db.get(Paciente, data["paciente"].id)
    # A minimal existing service is needed only to satisfy the appointment FK.
    from app.models.especialidad import Especialidad
    especialidad = Especialidad(nombre=f"Especialidad-{data['consultorio'].id}", activa=True)
    db.add(especialidad); db.flush()
    prestacion = Prestacion(profesional_id=member.id, especialidad_id=especialidad.id, nombre="Prestación sintética", duracion_minutos=30, precio=1, activa=True)
    db.add(prestacion); db.flush()
    turno = Turno(paciente_id=patient.id, prestacion_id=prestacion.id, profesional_id=member.id, fecha_hora=inicio + timedelta(hours=1), fecha_fin=inicio + timedelta(hours=1, minutes=30), estado="confirmado")
    db.add(turno); db.commit(); db.close()
    blocked = client.post(f"/consultorios/{data['consultorio'].id}/modulos/{creado.json()['id']}/suspender")
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["turnos_afectados"] == 1
    assert set(blocked.json()["detail"]) == {"mensaje", "turnos_afectados"}
    assert "sintético" not in blocked.text.lower()
    db = SessionTest()
    assert db.get(OcurrenciaModulo, creado.json()["id"]).estado == "activa"
    db.close()


def test_version_de_regla_bloquea_turnos_y_revela_solo_conteo(client, consultorio_modulos):
    data = consultorio_modulos
    regla_creada = _crear_regla(client, data, dia=3, hora="09:00:00")
    assert regla_creada.status_code == 201, regla_creada.text
    db = SessionTest()
    regla = db.query(ReglaRecurrenciaModulo).filter_by(id=regla_creada.json()["id"]).one()
    ocurrencia = db.query(OcurrenciaModulo).filter_by(regla_id=regla.id, estado="activa").order_by(OcurrenciaModulo.fecha_inicio).first()
    paciente = db.get(Paciente, data["paciente"].id)
    profesional = db.get(Profesional, data["pro_b"].id)
    from app.models.especialidad import Especialidad
    especialidad = Especialidad(nombre=f"Especialidad-cambio-{data['consultorio'].id}", activa=True)
    db.add(especialidad); db.flush()
    prestacion = Prestacion(profesional_id=profesional.id, especialidad_id=especialidad.id, nombre="Prestación cambio sintética", duracion_minutos=30, precio=1, activa=True)
    db.add(prestacion); db.flush()
    turno_inicio = desde_base_utc(ocurrencia.fecha_inicio) + timedelta(minutes=15)
    turno = Turno(paciente_id=paciente.id, prestacion_id=prestacion.id, profesional_id=profesional.id, fecha_hora=turno_inicio, fecha_fin=turno_inicio + timedelta(minutes=30), estado="reservado")
    db.add(turno); db.commit()
    rule_id = regla.id
    efectiva = regla.vigente_desde
    db.close()
    _autenticar(data["titular"])
    bloqueado = client.patch(
        f"/consultorios/{data['consultorio'].id}/reglas-modulo/{rule_id}",
        json={"vigente_desde": efectiva.isoformat(), "hora_inicio": "10:00:00", "profesional_id": data["pro_a"].id},
    )
    assert bloqueado.status_code == 409
    assert bloqueado.json()["detail"]["turnos_afectados"] == 1
    assert set(bloqueado.json()["detail"]) == {"mensaje", "turnos_afectados"}
    assert "paciente" not in bloqueado.text.lower()
    db = SessionTest()
    actual = db.get(ReglaRecurrenciaModulo, rule_id)
    assert actual.estado == "activa" and actual.hora_inicio == time(9)
    assert db.query(ReglaRecurrenciaModulo).count() == 1
    db.close()


def test_invitacion_prepara_modulos_token_hash_acepta_idempotente_y_no_filtra_token(client, consultorio_modulos, monkeypatch):
    from app.services import consultorio_invitacion_service as invitations
    from app.services.email_service import EmailDeliveryResult

    data = consultorio_modulos
    now = ahora_utc().astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    start = now + timedelta(days=1)
    while start.weekday() != 1:
        start += timedelta(days=1)
    user = Usuario(nombre="Invitada", email="invitada@example.com", password_hash="synthetic", rol="profesional", email_verificado=True)
    db = SessionTest(); db.add(user); db.flush()
    professional = Profesional(usuario_id=user.id, nombre="Invitada", apellido="Sintética", matricula=f"INV-{user.id}", email=user.email)
    db.add(professional); db.commit(); db.refresh(user); db.refresh(professional); db.close()

    sent = {}
    class CaptureProvider:
        def enviar(self, email):
            sent["text"] = email.texto
            return EmailDeliveryResult(provider="test")
    monkeypatch.setattr(invitations, "obtener_email_provider", lambda: CaptureProvider())
    _autenticar(data["titular"])
    payload = {
        "email": user.email,
        "nombre_visible": "Invitada Sintética",
        "modulos": [{"sala_id": data["sala"].id, "dia_semana": 1, "hora_inicio": "09:00:00", "vigente_desde": start.isoformat()}],
    }
    created = client.post(f"/consultorios/{data['consultorio'].id}/invitaciones", json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["estado"] == "preparacion"
    assert created.json()["modulos_reservados"] >= 12
    invite_id = created.json()["id"]
    listed = client.get(f"/consultorios/{data['consultorio'].id}/invitaciones")
    assert listed.status_code == 200
    assert "token" not in listed.text.lower()
    assert "token_hash" not in listed.text.lower()
    assert client.post(f"/consultorios/{data['consultorio'].id}/invitaciones/{invite_id}/enviar").status_code == 200
    assert "#token=" in sent["text"]
    previous_token = sent["text"].split("#token=", 1)[1].split()[0]
    assert client.post(f"/consultorios/{data['consultorio'].id}/invitaciones/{invite_id}/reenviar").status_code == 200
    token = sent["text"].split("#token=", 1)[1].split()[0]
    assert previous_token != token
    db = SessionTest(); invitation = db.get(InvitacionConsultorio, invite_id)
    assert invitation.token_hash != token
    assert invitation.token_hash == invitations._hash(token)
    db.close()
    _autenticar(user)
    assert client.post("/consultorios/aceptar-invitacion", json={"token": previous_token}).status_code == 400
    accepted = client.post("/consultorios/aceptar-invitacion", json={"token": token})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["profesional_vinculado"] is True
    assert client.get("/pacientes").status_code in {403, 404}
    assert client.get(f"/pacientes/{data['paciente'].id}").status_code in {403, 404}
    again = client.post("/consultorios/aceptar-invitacion", json={"token": token})
    assert again.status_code == 200
    db = SessionTest()
    invite = db.get(InvitacionConsultorio, invite_id)
    assert invite.estado == "aceptada" and invite.token_hash == invitations._hash(token)
    assert db.query(ConsultorioProfesional).filter_by(consultorio_id=data["consultorio"].id, profesional_id=professional.id, estado="activo").count() == 1
    assert db.query(OcurrenciaModulo).filter_by(invitacion_id=None, profesional_id=professional.id, estado="activa").count() >= 12
    db.close()


def test_invitacion_no_acepta_email_ajeno_y_revocar_invalida_token(client, consultorio_modulos, monkeypatch):
    from app.services import consultorio_invitacion_service as invitations
    from app.services.email_service import EmailDeliveryResult
    data = consultorio_modulos
    now = ahora_utc().astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    start = now + timedelta(days=1)
    while start.weekday() != 4:
        start += timedelta(days=1)
    sent = {}
    class CaptureProvider:
        def enviar(self, email):
            sent["text"] = email.texto
            return EmailDeliveryResult(provider="test")
    monkeypatch.setattr(invitations, "obtener_email_provider", lambda: CaptureProvider())
    _autenticar(data["titular"])
    result = client.post(f"/consultorios/{data['consultorio'].id}/invitaciones", json={"email": "ajeno@example.com", "modulos": [{"sala_id": data["sala"].id, "dia_semana": 4, "hora_inicio": "09:00:00", "vigente_desde": start.isoformat()}]})
    assert result.status_code == 201, result.text
    invite_id = result.json()["id"]
    assert client.post(f"/consultorios/{data['consultorio'].id}/invitaciones/{invite_id}/enviar").status_code == 200
    token = sent["text"].split("#token=", 1)[1].split()[0]
    _autenticar(data["miembro"])
    wrong = client.post("/consultorios/aceptar-invitacion", json={"token": token})
    assert wrong.status_code == 400
    _autenticar(data["titular"])
    revoked = client.post(f"/consultorios/{data['consultorio'].id}/invitaciones/{invite_id}/revocar")
    assert revoked.status_code == 200
    _autenticar(data["miembro"])
    assert client.post("/consultorios/aceptar-invitacion", json={"token": token}).status_code == 400


def test_invitaciones_reservan_cupo_y_rechazan_administracion_ajena(client, consultorio_modulos):
    data = consultorio_modulos
    db = SessionTest(); clinic = db.get(Consultorio, data["consultorio"].id); clinic.cupo_profesionales = 2
    db.query(ConsultorioProfesional).filter_by(consultorio_id=clinic.id, profesional_id=data["pro_b"].id).one().estado = "preparatorio"
    db.commit(); db.close()
    _autenticar(data["titular"])
    start = ahora_utc().astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date() + timedelta(days=1)
    while start.weekday() != 0:
        start += timedelta(days=1)
    payload = {"email": "cupo@example.com", "modulos": [{"sala_id": data["sala"].id, "dia_semana": 0, "hora_inicio": "14:00:00", "vigente_desde": start.isoformat()}]}
    first = client.post(f"/consultorios/{data['consultorio'].id}/invitaciones", json=payload)
    assert first.status_code == 201, first.text
    payload["email"] = "siguiente@example.com"
    second = client.post(f"/consultorios/{data['consultorio'].id}/invitaciones", json=payload)
    assert second.status_code == 409
    _autenticar(data["miembro"])
    assert client.get(f"/consultorios/{data['consultorio'].id}/invitaciones").status_code == 404


def test_ocupacion_de_invitacion_no_revela_nombre_como_profesional_activo(client, consultorio_modulos):
    data = consultorio_modulos
    _autenticar(data["titular"])
    start = ahora_utc().astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date() + timedelta(days=1)
    while start.weekday() != 5:
        start += timedelta(days=1)
    created = client.post(f"/consultorios/{data['consultorio'].id}/invitaciones", json={
        "email": "invitada-sintetica@example.com",
        "nombre_visible": "Nombre privado de invitada",
        "modulos": [{"sala_id": data["sala"].id, "dia_semana": 5, "hora_inicio": "14:00:00", "vigente_desde": start.isoformat()}],
    })
    assert created.status_code == 201, created.text
    listado = client.get(f"/consultorios/{data['consultorio'].id}/modulos")
    assert listado.status_code == 200
    pendiente = next(item for item in listado.json() if item["profesional_id"] is None)
    assert pendiente["profesional_nombre"] == "Invitación pendiente"
    assert "Nombre privado de invitada" not in listado.text
    assert "invitada-sintetica@example.com" not in listado.text


def test_reserva_de_invitacion_revocada_se_libera_y_no_aparece_en_ocupacion(client, consultorio_modulos):
    data = consultorio_modulos
    zona = ZoneInfo("America/Argentina/Buenos_Aires")
    fecha = ahora_utc().astimezone(zona).date() + timedelta(days=14)
    while fecha.weekday() != 4:
        fecha += timedelta(days=1)
    inicio = datetime.combine(fecha, time(13), tzinfo=zona)
    fin = inicio + timedelta(hours=4)

    _autenticar(data["titular"])
    creada = client.post(f"/consultorios/{data['consultorio'].id}/invitaciones", json={
        "email": "reserva-pendiente-sintetica@example.com",
        "nombre_visible": "Nombre sintético privado",
        "modulos": [{"sala_id": data["sala"].id, "dia_semana": fecha.weekday(), "hora_inicio": "13:00", "vigente_desde": fecha.isoformat()}],
    })
    assert creada.status_code == 201, creada.text
    invite_id = creada.json()["id"]
    desde = inicio.astimezone(UTC).isoformat()
    hasta = (inicio + timedelta(days=1)).astimezone(UTC).isoformat()
    ocupacion = client.get(f"/consultorios/{data['consultorio'].id}/modulos", params={"desde": desde, "hasta": hasta})
    assert ocupacion.status_code == 200
    pendiente = next(item for item in ocupacion.json() if item["profesional_id"] is None)
    assert pendiente["estado"] == "activa"
    assert pendiente["fecha_inicio"]
    assert "Nombre sintético privado" not in ocupacion.text
    assert "reserva-pendiente-sintetica" not in ocupacion.text
    assert not {"paciente", "turno_id", "historia_clinica"} & pendiente.keys()

    # Simula una fila histórica inconsistente: invitación terminal con ocurrencias todavía activas.
    db = SessionTest()
    invite = db.get(InvitacionConsultorio, invite_id)
    invite.estado = "revocada"
    invite.token_hash = None
    invite.revocada_en = ahora_utc()
    occurrence = db.query(OcurrenciaModulo).filter_by(invitacion_id=invite_id, estado="activa").first()
    occurrence_id = occurrence.id
    db.commit()
    db.close()

    ocupacion = client.get(f"/consultorios/{data['consultorio'].id}/modulos", params={"desde": desde, "hasta": hasta})
    assert ocupacion.status_code == 200
    assert all(item["id"] != occurrence_id for item in ocupacion.json())
    assert "Invitación pendiente" not in ocupacion.text
    db = SessionTest()
    assert db.get(InvitacionConsultorio, invite_id).estado == "revocada"
    assert db.query(OcurrenciaModulo).filter_by(invitacion_id=invite_id, estado="activa").count() == 0
    assert db.query(OcurrenciaModulo).filter_by(id=occurrence_id).one().estado == "cancelada"
    db.close()

    liberado = crear_modulo_extraordinario(
        (db := SessionTest()), data["titular"], data["consultorio"].id,
        ModuloExtraordinarioCrear(sala_id=data["sala"].id, profesional_id=data["pro_b"].id, fecha_inicio=inicio, fecha_fin=fin),
    )
    assert liberado.estado == "activa"
    db.close()

    fecha_vencida = ahora_utc().astimezone(zona).date() + timedelta(days=14)
    while fecha_vencida.weekday() != 6:
        fecha_vencida += timedelta(days=1)
    inicio_vencido = datetime.combine(fecha_vencida, time(14), tzinfo=zona)
    _autenticar(data["titular"])
    creada_vencida = client.post(f"/consultorios/{data['consultorio'].id}/invitaciones", json={
        "email": "reserva-expirada-sintetica@example.com",
        "modulos": [{"sala_id": data["sala"].id, "dia_semana": fecha_vencida.weekday(), "hora_inicio": "14:00", "vigente_desde": fecha_vencida.isoformat()}],
    })
    assert creada_vencida.status_code == 201, creada_vencida.text
    vencida_id = creada_vencida.json()["id"]
    db = SessionTest()
    invite_vencida = db.get(InvitacionConsultorio, vencida_id)
    invite_vencida.vence_en = ahora_utc() - timedelta(seconds=1)
    db.commit()
    db.close()
    vencimiento = client.get(f"/consultorios/{data['consultorio'].id}/modulos", params={
        "desde": inicio_vencido.astimezone(UTC).isoformat(),
        "hasta": (inicio_vencido + timedelta(days=1)).astimezone(UTC).isoformat(),
    })
    assert vencimiento.status_code == 200
    assert all(item["profesional_id"] is not None for item in vencimiento.json())
    db = SessionTest()
    assert db.get(InvitacionConsultorio, vencida_id).estado == "expirada"
    assert db.query(OcurrenciaModulo).filter_by(invitacion_id=vencida_id, estado="activa").count() == 0
    db.close()


def test_invitacion_vencida_invalida_token_y_libera_sala(client, consultorio_modulos, monkeypatch):
    from app.services import consultorio_invitacion_service as invitations
    from app.services.email_service import EmailDeliveryResult
    data = consultorio_modulos
    sent = {}
    class CaptureProvider:
        def enviar(self, email):
            sent["text"] = email.texto
            return EmailDeliveryResult(provider="test")
    monkeypatch.setattr(invitations, "obtener_email_provider", lambda: CaptureProvider())
    start = ahora_utc().astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date() + timedelta(days=1)
    while start.weekday() != 2:
        start += timedelta(days=1)
    _autenticar(data["titular"])
    created = client.post(f"/consultorios/{data['consultorio'].id}/invitaciones", json={"email": "vence@example.com", "modulos": [{"sala_id": data["sala"].id, "dia_semana": 2, "hora_inicio": "09:00:00", "vigente_desde": start.isoformat()}]})
    assert created.status_code == 201, created.text
    invite_id = created.json()["id"]
    assert client.post(f"/consultorios/{data['consultorio'].id}/invitaciones/{invite_id}/enviar").status_code == 200
    token = sent["text"].split("#token=", 1)[1].split()[0]
    db = SessionTest(); invite = db.get(InvitacionConsultorio, invite_id); invite.vence_en = ahora_utc() - timedelta(seconds=1); db.commit(); db.close()
    _autenticar(data["miembro"])
    assert client.post("/consultorios/aceptar-invitacion", json={"token": token}).status_code == 400
    db = SessionTest()
    invite = db.get(InvitacionConsultorio, invite_id)
    assert invite.estado == "expirada" and invite.token_hash is None
    assert db.query(OcurrenciaModulo).filter_by(invitacion_id=invite_id, estado="activa").count() == 0
    db.close()


def test_regla_se_reasigna_desde_fecha_futura_si_no_hay_turnos(client, consultorio_modulos):
    data = consultorio_modulos
    creada = _crear_regla(client, data, dia=4, hora="09:00:00")
    assert creada.status_code == 201, creada.text
    db = SessionTest()
    regla = db.get(ReglaRecurrenciaModulo, creada.json()["id"])
    regla_id = regla.id
    efectiva = regla.vigente_desde + timedelta(days=7)
    db.close()
    _autenticar(data["titular"])
    cambiada = client.patch(
        f"/consultorios/{data['consultorio'].id}/reglas-modulo/{regla_id}",
        json={"vigente_desde": efectiva.isoformat(), "profesional_id": data["pro_a"].id},
    )
    assert cambiada.status_code == 200, cambiada.text
    assert cambiada.json()["profesional_id"] == data["pro_a"].id
    assert cambiada.json()["serie_id"] != creada.json()["serie_id"]
    db = SessionTest()
    vieja = db.get(ReglaRecurrenciaModulo, regla_id)
    assert vieja.estado == "reemplazada" and vieja.vigente_hasta == efectiva - timedelta(days=1)
    db.close()


def test_validacion_turnos_vinculados_y_flujo_individual(monkeypatch):
    class FakeDB:
        def flush(self): pass
        def query(self, model):
            class Query:
                def filter(self, *args): return self
                def all(self): return []
            return Query()
    db = FakeDB()
    inicio = ahora_utc() + timedelta(days=3)
    llamado = []
    monkeypatch.setattr(consultorio_modulo_repository, "profesional_vinculado", lambda *_: False)
    monkeypatch.setattr(consultorio_modulo_repository, "buscar_ocurrencia_vigente_para_turno", lambda *args, **kwargs: llamado.append(True))
    validar_turno_en_modulo(db, 812, inicio, inicio + timedelta(minutes=30))
    assert llamado == []
    monkeypatch.setattr(consultorio_modulo_repository, "profesional_vinculado", lambda *_: True)
    monkeypatch.setattr(consultorio_modulo_repository, "buscar_ocurrencia_vigente_para_turno", lambda *args, **kwargs: None)
    with pytest.raises(HTTPException) as error:
        validar_turno_en_modulo(db, 812, inicio, inicio + timedelta(minutes=30))
    assert error.value.status_code == 409
    assert "módulo autorizado" in error.value.detail


def test_turnos_http_respetan_modulo_en_alta_y_reprogramacion(client, consultorio_modulos):
    data = consultorio_modulos
    respuesta = _crear_regla(client, data, dia=1, hora="09:00:00")
    assert respuesta.status_code == 201, respuesta.text
    db = SessionTest()
    miembro = db.get(Profesional, data["pro_b"].id)
    paciente = db.get(Paciente, data["paciente"].id)
    from app.models.regla_recurrencia_modulo import ReglaRecurrenciaModulo
    regla = db.query(ReglaRecurrenciaModulo).filter_by(serie_id=respuesta.json()["serie_id"]).one()
    ocurrencias = db.query(OcurrenciaModulo).filter_by(regla_id=regla.id, estado="activa").order_by(OcurrenciaModulo.fecha_inicio).limit(2).all()
    inicios = [desde_base_utc(item.fecha_inicio) for item in ocurrencias]
    especialidad = Especialidad(nombre=f"Especialidad-turnos-{data['consultorio'].id}", activa=True)
    db.add(especialidad); db.flush()
    prestacion = Prestacion(profesional_id=miembro.id, especialidad_id=especialidad.id, nombre="Atención sintética", duracion_minutos=30, precio=1, activa=True)
    db.add_all([prestacion, ProfesionalPaciente(profesional_id=miembro.id, paciente_id=paciente.id), Disponibilidad(profesional_id=miembro.id, dia_semana=1, hora_inicio=time(8), hora_fin=time(18), activa=True)])
    db.commit()
    prestacion_id = prestacion.id
    db.close()
    _autenticar(data["miembro"])
    inicio = inicios[0] + timedelta(minutes=15)
    dentro = client.post("/profesionales/me/turnos", json={"paciente_id": data["paciente"].id, "prestacion_id": prestacion_id, "fecha_hora": inicio.isoformat()})
    assert dentro.status_code == 201, dentro.text
    fuera = client.post("/profesionales/me/turnos", json={"paciente_id": data["paciente"].id, "prestacion_id": prestacion_id, "fecha_hora": (inicio.replace(hour=17, minute=0)).isoformat()})
    assert fuera.status_code == 409
    assert "módulo autorizado" in fuera.json()["detail"]
    segundo_inicio = inicios[1] + timedelta(minutes=15)
    segundo = client.post("/profesionales/me/turnos", json={"paciente_id": data["paciente"].id, "prestacion_id": prestacion_id, "fecha_hora": segundo_inicio.isoformat()})
    assert segundo.status_code == 201, segundo.text
    reprogramacion = client.patch(f"/profesionales/me/agenda/{segundo.json()['id']}/reprogramar", json={"fecha_hora": segundo_inicio.replace(hour=17, minute=0).isoformat()})
    assert reprogramacion.status_code == 409
    assert "módulo autorizado" in reprogramacion.json()["detail"]


def test_solapamiento_semanal_admite_adyacencia_y_detecta_cruce_entre_dias():
    desde = date(2027, 1, 4)  # Monday
    assert not _fechas_solapan_reglas(0, time(9), 240, desde, None, 0, time(13), 240, desde, None)
    assert _fechas_solapan_reglas(0, time(22), 240, desde, None, 1, time(1), 120, desde, None)


def test_conversion_dst_salta_hora_inexistente_y_elige_primer_fold():
    zona = ZoneInfo("America/New_York")
    assert _instante_local_utc(date(2027, 3, 14), time(2, 30), zona) is None
    primer_fold = _instante_local_utc(date(2027, 11, 7), time(1, 30), zona)
    assert primer_fold == datetime(2027, 11, 7, 5, 30, tzinfo=UTC)


def test_profesional_consulta_solo_sus_modulos_activos_en_estados_preparatorio_y_activo(client, consultorio_modulos):
    data = consultorio_modulos
    inicio = ahora_utc() + timedelta(days=8)
    db = SessionTest()
    _agregar_ocurrencia(db, data, data["pro_a"], inicio)
    ajeno = _agregar_ocurrencia(db, data, data["pro_a"], inicio + timedelta(hours=5))
    propio_activo = _agregar_ocurrencia(db, data, data["pro_b"], inicio + timedelta(hours=10))
    suspendido = _agregar_ocurrencia(db, data, data["pro_b"], inicio + timedelta(hours=15), estado="suspendida")
    inicio_ajeno = desde_base_utc(ajeno.fecha_inicio)
    inicio_propio_activo = desde_base_utc(propio_activo.fecha_inicio)
    suspendido_id = suspendido.id
    db.commit()
    total_antes = db.query(OcurrenciaModulo).count()
    db.close()

    _autenticar(data["titular"])
    titular = client.get("/profesionales/me/consultorio/modulos")
    assert titular.status_code == 200, titular.text
    assert len(titular.json()) == 2
    assert all(set(row) == {"sala_id", "sala_nombre", "fecha_inicio", "fecha_fin", "estado"} for row in titular.json())
    assert all(row["sala_nombre"] == "Sala piloto" and row["estado"] == "activa" for row in titular.json())
    assert all(not {"profesional_id", "profesional_nombre", "paciente_id", "turno_id", "historia_clinica", "regla_id", "consultorio_id"} & row.keys() for row in titular.json())

    _autenticar(data["miembro"])
    miembro = client.get("/profesionales/me/consultorio/modulos")
    assert miembro.status_code == 200, miembro.text
    assert len(miembro.json()) == 1
    inicio_respuesta = datetime.fromisoformat(miembro.json()[0]["fecha_inicio"]).replace(tzinfo=UTC)
    assert inicio_respuesta == inicio_propio_activo
    assert inicio_respuesta != inicio_ajeno
    assert all(row["estado"] == "activa" for row in miembro.json())
    db = SessionTest()
    assert db.query(OcurrenciaModulo).count() == total_antes  # GET did not materialize or modify rows.
    assert db.get(OcurrenciaModulo, suspendido_id).estado == "suspendida"
    db.close()


def test_endpoint_profesional_requiere_autenticacion_y_rol_profesional(client, consultorio_modulos):
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    assert client.get("/profesionales/me/consultorio/modulos").status_code == 401

    db = SessionTest()
    usuario_paciente = Usuario(nombre="Paciente", email="paciente-modulos@test.invalid", password_hash="fixture", rol="paciente")
    db.add(usuario_paciente)
    db.commit()
    db.refresh(usuario_paciente)
    _autenticar(usuario_paciente)
    respuesta = client.get("/profesionales/me/consultorio/modulos")
    assert respuesta.status_code == 403
    assert "módulos" not in respuesta.text.lower()
    db.close()


def test_profesional_no_accede_a_rutas_administrativas_ni_puede_mutar_sus_modulos(client, consultorio_modulos):
    data = consultorio_modulos
    _autenticar(data["miembro"])
    consultorio_id = data["consultorio"].id
    ahora = ahora_utc()
    inicio = (ahora + timedelta(days=10)).replace(minute=0, second=0, microsecond=0)
    payload_regla = {"sala_id": data["sala"].id, "profesional_id": data["pro_b"].id, "dia_semana": inicio.weekday(), "hora_inicio": "10:00:00", "vigente_desde": inicio.date().isoformat()}
    payload_extra = {"sala_id": data["sala"].id, "profesional_id": data["pro_b"].id, "fecha_inicio": inicio.isoformat(), "fecha_fin": (inicio + timedelta(hours=4)).isoformat()}

    assert client.get(f"/consultorios/{consultorio_id}/modulos").status_code == 404
    assert client.post(f"/consultorios/{consultorio_id}/reglas-modulo", json=payload_regla).status_code == 404
    assert client.patch(f"/consultorios/{consultorio_id}/reglas-modulo/999", json={"vigente_desde": inicio.date().isoformat(), "hora_inicio": "11:00:00"}).status_code == 404
    assert client.post(f"/consultorios/{consultorio_id}/modulos-extraordinarios", json=payload_extra).status_code == 404
    assert client.patch(f"/consultorios/{consultorio_id}/modulos/999", json={"fecha_inicio": (inicio + timedelta(hours=1)).isoformat()}).status_code == 404
    assert client.post(f"/consultorios/{consultorio_id}/modulos/999/suspender").status_code == 404
    assert client.post("/profesionales/me/consultorio/modulos").status_code == 405

    db = SessionTest()
    assert db.query(ReglaRecurrenciaModulo).count() == 0
    assert db.query(OcurrenciaModulo).count() == 0
    db.close()
