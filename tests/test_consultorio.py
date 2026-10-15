from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.clinical_profile import ClinicalProfile
from app.models.consultorio import Consultorio
from app.models.consultorio_administrador import ConsultorioAdministrador
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.evolucion_clinica import EvolucionClinica
from app.models.paciente import Paciente
from app.models.patient_document import PatientDocument
from app.models.profesional import Profesional
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.sala import Sala
from app.models.study_request import StudyRequest
from app.models.usuario import Usuario
from tests.conftest import SessionTest


@pytest.fixture
def escenario_consultorio(client):
    db = SessionTest()
    propietario = Usuario(nombre="Titular sintética", email="titular@consultorio.test", password_hash="solo-fixture", rol="profesional")
    profesional = Usuario(nombre="Integrante sintético", email="integrante@consultorio.test", password_hash="solo-fixture", rol="profesional")
    db.add_all([propietario, profesional]); db.flush()
    pro_a = Profesional(usuario_id=propietario.id, nombre="Titular", apellido="Sintética", matricula="CONS-TITULAR")
    pro_b = Profesional(usuario_id=profesional.id, nombre="Integrante", apellido="Sintético", matricula="CONS-MIEMBRO")
    cuenta_consultorio = Cuenta(nombre="Cuenta organizacional sintética", tipo="organizacion")
    paciente = Paciente(nombre="Paciente", apellido="Sintético", activo=True)
    db.add_all([pro_a, pro_b, cuenta_consultorio, paciente]); db.flush()
    consultorio = Consultorio(cuenta_id=cuenta_consultorio.id, nombre="Consultorio sintético")
    db.add(consultorio); db.flush()
    db.add_all([
        ConsultorioAdministrador(consultorio_id=consultorio.id, usuario_id=propietario.id, rol="propietaria"),
        ConsultorioProfesional(consultorio_id=consultorio.id, profesional_id=pro_b.id, estado="activo"),
        ProfesionalPaciente(profesional_id=pro_a.id, paciente_id=paciente.id),
        ProfesionalPaciente(profesional_id=pro_b.id, paciente_id=paciente.id),
        ClinicalProfile(paciente_id=paciente.id, profesional_id=pro_b.id, updated_by_profesional_id=pro_b.id, antecedentes="Solo visible para integrante"),
        EvolucionClinica(paciente_id=paciente.id, profesional_id=pro_b.id, contenido="Evolución confidencial sintética"),
        PatientDocument(paciente_id=paciente.id, profesional_id=pro_b.id, uploaded_by_profesional_id=pro_b.id, storage_key="synthetic/consultorio/private.pdf", original_filename="sintetico.pdf", mime_type="application/pdf", category="other", status="available"),
        StudyRequest(paciente_id=paciente.id, profesional_id=pro_b.id, title="Estudio sintético privado", status="pending", requested_at=datetime.now(timezone.utc)),
        Sala(consultorio_id=consultorio.id, nombre="Sala uno", codigo="SALA-1"),
    ])
    cuenta_individual_original = pro_a.cuenta_id
    db.commit()
    valores = {
        "propietario": propietario,
        "profesional": profesional,
        "pro_a": pro_a,
        "pro_b": pro_b,
        "cuenta_individual_original": cuenta_individual_original,
        "cuenta_consultorio_id": cuenta_consultorio.id,
        "consultorio": consultorio,
        "paciente": paciente,
    }
    yield valores
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    db.close()


def autenticar(usuario: Usuario):
    app.dependency_overrides[obtener_usuario_actual] = lambda: usuario


def test_admin_consultorio_gestiona_configuracion_salas_sin_enumerar_ajenos(client, escenario_consultorio):
    data = escenario_consultorio
    autenticar(data["propietario"])
    consultorio_id = data["consultorio"].id
    assert client.get("/consultorios").json()[0]["id"] == consultorio_id
    respuesta = client.get(f"/consultorios/{consultorio_id}")
    assert respuesta.status_code == 200
    assert respuesta.json()["duracion_modulo_minutos"] == 240
    assert respuesta.json()["horizonte_materializacion_dias"] == 90
    assert "cuenta_id" not in respuesta.json()

    respuesta = client.patch(f"/consultorios/{consultorio_id}", json={"zona_horaria": "America/Argentina/Cordoba", "duracion_modulo_minutos": 180})
    assert respuesta.status_code == 200
    assert respuesta.json()["zona_horaria"] == "America/Argentina/Cordoba"
    assert respuesta.json()["duracion_modulo_minutos"] == 180
    assert client.patch(f"/consultorios/{consultorio_id}", json={"zona_horaria": "Not/AZone"}).status_code == 422
    assert client.patch(f"/consultorios/{consultorio_id}", json={"cuenta_id": data["cuenta_consultorio_id"]}).status_code == 422
    assert client.patch(f"/consultorios/{consultorio_id}", json={"nombre": None}).status_code == 422

    salas = client.get(f"/consultorios/{consultorio_id}/salas")
    assert salas.status_code == 200 and [item["codigo"] for item in salas.json()] == ["SALA-1"]
    creada = client.post(f"/consultorios/{consultorio_id}/salas", json={"nombre": "Sala dos", "codigo": "SALA-2"})
    assert creada.status_code == 201
    assert client.post(f"/consultorios/{consultorio_id}/salas", json={"nombre": "Duplicada", "codigo": "SALA-2"}).status_code == 409
    assert client.patch(f"/consultorios/{consultorio_id}/salas/{creada.json()['id']}", json={"estado": "inactiva"}).json()["estado"] == "inactiva"
    assert client.patch(f"/consultorios/{consultorio_id}/salas/{creada.json()['id']}", json={"codigo": None}).status_code == 422

    # El consultorio ajeno y su sala se crean mediante otra sesión para representar el límite de ownership.
    db = SessionTest()
    otra_cuenta = Cuenta(nombre="Cuenta ajena sintética", tipo="organizacion")
    db.add(otra_cuenta); db.flush()
    otro_consultorio = Consultorio(cuenta_id=otra_cuenta.id, nombre="Consultorio ajeno")
    db.add(otro_consultorio); db.flush()
    db.add(CuentaUsuario(cuenta_id=otra_cuenta.id, usuario_id=data["propietario"].id, rol_cuenta="propietario"))
    otra_sala = Sala(consultorio_id=otro_consultorio.id, nombre="Sala privada", codigo="PRIVADA")
    db.add(otra_sala); db.commit()
    assert client.get(f"/consultorios/{otro_consultorio.id}").status_code == 404
    assert client.patch(f"/consultorios/{otro_consultorio.id}", json={"nombre": "Intrusión"}).status_code == 404
    assert client.get(f"/consultorios/{otro_consultorio.id}/salas").status_code == 404
    assert client.patch(f"/consultorios/{consultorio_id}/salas/{otra_sala.id}", json={"nombre": "Intrusión"}).status_code == 404
    db.close()
    db = SessionTest()
    assert db.get(Consultorio, otro_consultorio.id).nombre == "Consultorio ajeno"
    db.close()


def test_lecturas_administrativas_minimas_exigen_admin_y_no_exponen_contactos(client, escenario_consultorio):
    data = escenario_consultorio
    clinic_id = data["consultorio"].id
    autenticar(data["propietario"])

    miembros = client.get(f"/consultorios/{clinic_id}/profesionales")
    assert miembros.status_code == 200
    assert miembros.json() == [{
        "profesional_id": data["pro_b"].id,
        "nombre": "Integrante Sintético",
        "estado": "activo",
    }]
    assert not {"email", "telefono", "matricula", "pacientes", "turnos"}.intersection(miembros.json()[0])

    db = SessionTest()
    room_id = db.query(Sala.id).filter_by(consultorio_id=clinic_id).scalar()
    db.close()
    inicio = date.today() + timedelta(days=7)
    inicio += timedelta(days=(0 - inicio.weekday()) % 7)
    regla = client.post(f"/consultorios/{clinic_id}/reglas-modulo", json={
        "sala_id": room_id,
        "profesional_id": data["pro_b"].id,
        "dia_semana": inicio.weekday(),
        "hora_inicio": "09:00:00",
        "vigente_desde": inicio.isoformat(),
    })
    assert regla.status_code == 201
    lecturas = client.get(f"/consultorios/{clinic_id}/reglas-modulo")
    assert lecturas.status_code == 200
    assert lecturas.json()[0]["profesional_nombre"] == "Integrante Sintético"
    assert lecturas.json()[0]["sala_nombre"] == "Sala uno"
    assert not {"email", "pacientes", "turnos", "documentos", "evoluciones"}.intersection(lecturas.json()[0])

    autenticar(data["profesional"])
    assert client.get(f"/consultorios/{clinic_id}/profesionales").status_code == 404
    assert client.get(f"/consultorios/{clinic_id}/reglas-modulo").status_code == 404
    assert client.get(f"/consultorios/{clinic_id}/modulos").status_code == 404


def test_crear_consultorio_exige_propiedad_organizacional_y_conserva_cuenta_profesional(client, escenario_consultorio):
    data = escenario_consultorio
    db = SessionTest()
    cuenta = Cuenta(nombre="Organización propia sintética", tipo="organizacion")
    cuenta_ajena = Cuenta(nombre="Organización ajena sintética", tipo="organizacion")
    cuenta_individual = db.get(Profesional, data["pro_a"].id).cuenta
    db.add_all([cuenta, cuenta_ajena]); db.flush()
    db.add(CuentaUsuario(cuenta_id=cuenta.id, usuario_id=data["propietario"].id, rol_cuenta="propietario"))
    db.commit()
    cuenta_id, cuenta_ajena_id, individual_id = cuenta.id, cuenta_ajena.id, cuenta_individual.id
    db.close()

    autenticar(data["propietario"])
    respuesta = client.post("/consultorios", json={"cuenta_id": cuenta_id, "nombre": "Nuevo consultorio", "duracion_modulo_minutos": 240})
    assert respuesta.status_code == 201
    consultorio_id = respuesta.json()["id"]
    assert client.post("/consultorios", json={"cuenta_id": cuenta_ajena_id, "nombre": "Ajeno"}).status_code == 404
    assert client.post("/consultorios", json={"cuenta_id": individual_id, "nombre": "Individual"}).status_code == 404
    assert client.post("/consultorios", json={"cuenta_id": cuenta_id, "nombre": "Duplicado"}).status_code == 409
    db = SessionTest()
    assert db.get(Profesional, data["pro_a"].id).cuenta_id == individual_id
    assert db.query(ConsultorioAdministrador).filter_by(consultorio_id=consultorio_id, usuario_id=data["propietario"].id, rol="propietaria").count() == 1
    db.close()


def test_asignacion_al_consultorio_no_cambia_cuenta_ni_ownership_clinico(client, escenario_consultorio):
    data = escenario_consultorio
    autenticar(data["propietario"])
    paciente_id = data["paciente"].id

    perfil = client.get(f"/pacientes/{paciente_id}/clinical-profile")
    assert perfil.status_code == 200
    assert perfil.json()["id"] is None
    assert perfil.json()["antecedentes"] is None
    assert client.get("/pacientes/").status_code == 403
    assert client.get("/turnos/").status_code == 403
    assert client.put(f"/pacientes/{paciente_id}/clinical-profile", json={"antecedentes": "Registro exclusivo de titular"}).status_code == 200
    assert client.get(f"/pacientes/{paciente_id}/evoluciones").json() == []
    assert client.post(f"/pacientes/{paciente_id}/evoluciones", json={"contenido": "Evolución propia sintética"}).status_code == 201
    assert client.get(f"/pacientes/{paciente_id}/documents").json() == []
    db = SessionTest()
    document_id = db.query(PatientDocument.id).filter_by(paciente_id=paciente_id, profesional_id=data["pro_b"].id).scalar()
    db.close()
    assert client.post(f"/pacientes/{paciente_id}/documents/{document_id}/download-url").status_code == 404
    assert client.get(f"/pacientes/{paciente_id}/study-requests").json() == []

    db = SessionTest()
    study_request_id = db.query(StudyRequest.id).filter_by(paciente_id=paciente_id, profesional_id=data["pro_b"].id).scalar()
    assert db.query(ClinicalProfile).filter_by(paciente_id=paciente_id, profesional_id=data["pro_b"].id).one().antecedentes == "Solo visible para integrante"
    assert db.query(EvolucionClinica).filter_by(paciente_id=paciente_id, profesional_id=data["pro_b"].id).one().contenido == "Evolución confidencial sintética"
    assert db.query(PatientDocument).filter_by(paciente_id=paciente_id, profesional_id=data["pro_b"].id).count() == 1
    assert db.query(StudyRequest).filter_by(paciente_id=paciente_id, profesional_id=data["pro_b"].id).count() == 1
    assert db.get(Profesional, data["pro_b"].id).cuenta_id == data["pro_b"].cuenta_id
    assert db.get(Profesional, data["pro_a"].id).cuenta_id == data["cuenta_individual_original"]
    assert db.query(ConsultorioProfesional).filter_by(profesional_id=data["pro_b"].id).one().estado == "activo"
    db.close()
    assert client.get(f"/pacientes/{paciente_id}/study-requests/{study_request_id}").status_code == 404


def test_vinculo_profesional_no_concede_administracion_y_no_hay_rutas_de_alta(client, escenario_consultorio):
    data = escenario_consultorio
    autenticar(data["profesional"])
    consultorio_id = data["consultorio"].id
    assert client.get(f"/consultorios/{consultorio_id}").status_code == 404
    assert client.post(f"/consultorios/{consultorio_id}/salas", json={"nombre": "No permitida", "codigo": "NO"}).status_code == 404
    assert client.post(f"/consultorios/{consultorio_id}/profesionales", json={"profesional_id": data["pro_b"].id}).status_code == 405


def test_restricciones_de_unicidad_en_modelos_sinteticos(client, escenario_consultorio):
    data = escenario_consultorio
    db = SessionTest()
    db.add(Sala(consultorio_id=data["consultorio"].id, nombre="Repetida", codigo="SALA-1"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.add(ConsultorioProfesional(consultorio_id=data["consultorio"].id, profesional_id=data["pro_b"].id, estado="preparatorio"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.close()
