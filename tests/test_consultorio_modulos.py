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
from app.repositories import consultorio_modulo_repository
from app.services.consultorio_modulo_service import (
    _fechas_solapan_reglas,
    _instante_local_utc,
    validar_turno_en_modulo,
)
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
