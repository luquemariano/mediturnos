from decimal import Decimal
from tests.conftest import SessionTest
from app.models.especialidad import Especialidad
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_especialidad import ProfesionalEspecialidad

def escenario(db):
    e = Especialidad(nombre="F11C Cardiología", duracion_turno_minutos=30)
    a = Profesional(nombre="Laura", apellido="Gómez", matricula="F11C-A", reserva_online_activa=True, slug_publico="laura-gomez-a1b2")
    b = Profesional(nombre="Mario", apellido="López", matricula="F11C-B", reserva_online_activa=True, slug_publico="mario-lopez-c3d4")
    db.add_all([e, a, b]); db.flush()
    db.add_all([ProfesionalEspecialidad(profesional_id=a.id, especialidad_id=e.id), ProfesionalEspecialidad(profesional_id=b.id, especialidad_id=e.id)])
    items = [
        Prestacion(nombre="Visible", descripcion="Consulta", duracion_minutos=30, precio=100, modalidad="presencial", profesional_id=a.id, especialidad_id=e.id, activa=True, habilitada_online=True),
        Prestacion(nombre="Deshabilitada", duracion_minutos=30, precio=100, modalidad="presencial", profesional_id=a.id, especialidad_id=e.id, activa=True, habilitada_online=False),
        Prestacion(nombre="Inactiva", duracion_minutos=30, precio=100, modalidad="presencial", profesional_id=a.id, especialidad_id=e.id, activa=False, habilitada_online=True),
        Prestacion(nombre="Ajena", duracion_minutos=30, precio=100, modalidad="presencial", profesional_id=b.id, especialidad_id=e.id, activa=True, habilitada_online=True),
    ]
    db.add_all(items); db.commit(); db.refresh(items[0]); return a, b, items

def test_perfil_publico_es_anonimo_y_seguro(client):
    db=SessionTest(); a, _, _ = escenario(db)
    respuesta=client.get(f"/public/profesionales/{a.slug_publico}")
    assert respuesta.status_code == 200
    data=respuesta.json(); assert data["nombre"] == "Laura" and data["especialidades"] == [{"nombre": "F11C Cardiología"}]
    for campo in ("id","profesional_id","cuenta_id","usuario_id","matricula","email","telefono","activo","onboarding_step","pacientes","turnos"):
        assert campo not in data
    db.close()

def test_perfil_publico_404_uniforme_y_no_requiere_auth(client):
    db=SessionTest(); a, b, _ = escenario(db); a.activo=False; db.commit()
    assert client.get(f"/public/profesionales/{a.slug_publico}").status_code == 404
    b.reserva_online_activa=False; db.commit()
    assert client.get(f"/public/profesionales/{b.slug_publico}").status_code == 404
    assert client.get("/public/profesionales/no-existe").status_code == 404
    assert client.get("/public/profesionales/LAURA-GOMEZ-A1B2").status_code == 404
    db.close()

def test_prestaciones_publicas_filtran_estado_y_profesional(client):
    db=SessionTest(); a, b, items = escenario(db)
    respuesta=client.get(f"/public/profesionales/{a.slug_publico}/prestaciones")
    assert respuesta.status_code == 200; data=respuesta.json(); assert [x["nombre"] for x in data] == ["Visible"]
    for campo in ("id","profesional_id","especialidad_id","precio","activa","habilitada_online","cuenta_id"):
        assert campo not in data[0]
    assert client.get(f"/public/profesionales/{b.slug_publico}/prestaciones").json()[0]["nombre"] == "Ajena"
    db.close()

def test_sin_prestaciones_habilitadas_devuelve_lista_vacia(client):
    db=SessionTest(); a, _, items = escenario(db)
    items[0].habilitada_online=False; db.commit()
    assert client.get(f"/public/profesionales/{a.slug_publico}/prestaciones").json() == []
    db.close()
