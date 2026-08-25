from datetime import date, time, timedelta
from types import SimpleNamespace

import pytest

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.usuario import Usuario
from app.routers import disponibilidades, especialidades


ROLES = (
    "administrador",
    "recepcionista",
    "profesional",
    "paciente",
)


@pytest.fixture
def usuarios():
    return {
        rol: Usuario(
            id=indice,
            nombre=rol.title(),
            email=f"{rol}@example.com",
            password_hash="hash",
            rol=rol,
            activo=True,
        )
        for indice, rol in enumerate(ROLES, start=1)
    }


@pytest.fixture(autouse=True)
def limpiar_usuario_autenticado():
    yield
    app.dependency_overrides.pop(
        obtener_usuario_actual,
        None,
    )


def autenticar_como(usuario):
    app.dependency_overrides[
        obtener_usuario_actual
    ] = lambda: usuario


def especialidad_respuesta():
    return SimpleNamespace(
        id=1,
        nombre="Clínica Médica",
        descripcion=None,
        duracion_turno_minutos=30,
        activa=True,
    )


def disponibilidad_respuesta(profesional_id=10):
    return SimpleNamespace(
        id=1,
        profesional_id=profesional_id,
        dia_semana=0,
        hora_inicio=time(9, 0),
        hora_fin=time(12, 0),
        activa=True,
    )


@pytest.mark.parametrize("rol", ROLES)
@pytest.mark.parametrize(
    "ruta",
    [
        "/especialidades/",
        "/especialidades/1",
    ],
)
def test_especialidades_permite_consulta_autenticada(
    client,
    usuarios,
    monkeypatch,
    rol,
    ruta,
):
    autenticar_como(usuarios[rol])
    monkeypatch.setattr(
        especialidades,
        "obtener_especialidades",
        lambda db: [especialidad_respuesta()],
    )
    monkeypatch.setattr(
        especialidades,
        "obtener_especialidad_por_id",
        lambda db, especialidad_id: especialidad_respuesta(),
    )

    respuesta = client.get(ruta)

    assert respuesta.status_code == 200


@pytest.mark.parametrize(
    "metodo,ruta,payload",
    [
        (
            "post",
            "/especialidades/",
            {
                "nombre": "Clínica Médica",
                "duracion_turno_minutos": 30,
            },
        ),
        (
            "patch",
            "/especialidades/1",
            {"activa": False},
        ),
    ],
)
def test_especialidades_solo_administrador_gestiona(
    client,
    usuarios,
    monkeypatch,
    metodo,
    ruta,
    payload,
):
    autenticar_como(usuarios["administrador"])
    objeto = especialidad_respuesta()
    monkeypatch.setattr(
        especialidades,
        "crear_especialidad",
        lambda db, datos: objeto,
    )
    monkeypatch.setattr(
        especialidades,
        "obtener_especialidad_por_id",
        lambda db, especialidad_id: objeto,
    )
    monkeypatch.setattr(
        especialidades,
        "modificar_especialidad",
        lambda db, especialidad, datos: objeto,
    )

    respuesta = getattr(client, metodo)(ruta, json=payload)

    assert respuesta.status_code in {200, 201}


@pytest.mark.parametrize(
    "rol",
    [
        "recepcionista",
        "profesional",
        "paciente",
    ],
)
@pytest.mark.parametrize(
    "metodo,ruta,payload",
    [
        (
            "post",
            "/especialidades/",
            {
                "nombre": "Clínica Médica",
                "duracion_turno_minutos": 30,
            },
        ),
        (
            "patch",
            "/especialidades/1",
            {"activa": False},
        ),
    ],
)
def test_especialidades_rechaza_gestion_no_administrativa(
    client,
    usuarios,
    rol,
    metodo,
    ruta,
    payload,
):
    autenticar_como(usuarios[rol])

    respuesta = getattr(client, metodo)(ruta, json=payload)

    assert respuesta.status_code == 403


@pytest.mark.parametrize(
    "rol",
    [
        "administrador",
        "recepcionista",
    ],
)
def test_personal_autorizado_lista_disponibilidades_globales(
    client,
    usuarios,
    monkeypatch,
    rol,
):
    autenticar_como(usuarios[rol])
    monkeypatch.setattr(
        disponibilidades,
        "obtener_disponibilidades",
        lambda db: [],
    )

    respuesta = client.get("/disponibilidades/")

    assert respuesta.status_code == 200


@pytest.mark.parametrize(
    "rol",
    [
        "profesional",
        "paciente",
    ],
)
def test_disponibilidades_globales_rechazan_acceso(
    client,
    usuarios,
    rol,
):
    autenticar_como(usuarios[rol])

    respuesta = client.get("/disponibilidades/")

    assert respuesta.status_code == 403


@pytest.mark.parametrize(
    "rol",
    [
        "administrador",
        "recepcionista",
    ],
)
def test_personal_autorizado_crea_disponibilidad(
    client,
    usuarios,
    monkeypatch,
    rol,
):
    autenticar_como(usuarios[rol])
    monkeypatch.setattr(
        disponibilidades,
        "crear_disponibilidad",
        lambda db, datos: disponibilidad_respuesta(
            datos.profesional_id
        ),
    )

    respuesta = client.post(
        "/disponibilidades/",
        json={
            "profesional_id": 10,
            "dia_semana": 0,
            "hora_inicio": "09:00:00",
            "hora_fin": "12:00:00",
        },
    )

    assert respuesta.status_code == 201


def test_profesional_gestiona_solo_su_disponibilidad(
    client,
    usuarios,
    monkeypatch,
):
    autenticar_como(usuarios["profesional"])
    monkeypatch.setattr(
        disponibilidades,
        "obtener_mi_profesional",
        lambda db, usuario_id: SimpleNamespace(id=10),
    )
    monkeypatch.setattr(
        disponibilidades,
        "crear_disponibilidad",
        lambda db, datos: disponibilidad_respuesta(
            datos.profesional_id
        ),
    )
    monkeypatch.setattr(
        disponibilidades,
        "obtener_disponibilidades_profesional",
        lambda db, profesional_id: [],
    )
    payload = {
        "profesional_id": 10,
        "dia_semana": 0,
        "hora_inicio": "09:00:00",
        "hora_fin": "12:00:00",
    }

    respuesta_crear = client.post(
        "/disponibilidades/",
        json=payload,
    )
    respuesta_consultar = client.get(
        "/disponibilidades/profesional/10"
    )
    payload["profesional_id"] = 11
    respuesta_crear_ajena = client.post(
        "/disponibilidades/",
        json=payload,
    )
    respuesta_consultar_ajena = client.get(
        "/disponibilidades/profesional/11"
    )

    assert respuesta_crear.status_code == 201
    assert respuesta_consultar.status_code == 200
    assert respuesta_crear_ajena.status_code == 403
    assert respuesta_consultar_ajena.status_code == 403


@pytest.mark.parametrize("rol", ROLES)
def test_horarios_libres_permite_consulta_autenticada(
    client,
    usuarios,
    monkeypatch,
    rol,
):
    autenticar_como(usuarios[rol])
    monkeypatch.setattr(
        disponibilidades,
        "obtener_horarios_libres",
        lambda db, prestacion_id, fecha, turno_id_excluido=None: [],
    )
    fecha = (date.today() + timedelta(days=1)).isoformat()

    respuesta = client.get(
        "/disponibilidades/horarios-libres/",
        params={
            "prestacion_id": 1,
            "fecha": fecha,
        },
    )

    assert respuesta.status_code == 200


@pytest.mark.parametrize(
    "rol",
    ["administrador", "recepcionista"],
)
def test_personal_autorizado_excluye_turno_en_horarios_libres(
    client,
    usuarios,
    monkeypatch,
    rol,
):
    autenticar_como(usuarios[rol])
    parametros_recibidos = {}

    def horarios(
        db,
        prestacion_id,
        fecha,
        turno_id_excluido=None,
    ):
        parametros_recibidos["turno_id_excluido"] = (
            turno_id_excluido
        )
        return []

    monkeypatch.setattr(
        disponibilidades,
        "obtener_horarios_libres",
        horarios,
    )

    respuesta = client.get(
        "/disponibilidades/horarios-libres/",
        params={
            "prestacion_id": 1,
            "fecha": "2030-01-01",
            "turno_id_excluido": 25,
        },
    )

    assert respuesta.status_code == 200
    assert parametros_recibidos["turno_id_excluido"] == 25


def test_paciente_no_puede_excluir_turno(
    client,
    usuarios,
):
    autenticar_como(usuarios["paciente"])

    respuesta = client.get(
        "/disponibilidades/horarios-libres/",
        params={
            "prestacion_id": 1,
            "fecha": "2030-01-01",
            "turno_id_excluido": 25,
        },
    )

    assert respuesta.status_code == 403
    assert respuesta.json() == {
        "detail": "Permisos insuficientes."
    }


def test_profesional_solo_excluye_un_turno_propio_de_la_misma_prestacion(
    client,
    usuarios,
    monkeypatch,
):
    autenticar_como(usuarios["profesional"])
    monkeypatch.setattr(
        disponibilidades,
        "obtener_mi_profesional",
        lambda *args: SimpleNamespace(id=10),
    )
    monkeypatch.setattr(
        disponibilidades,
        "buscar_turno_de_profesional",
        lambda db, turno_id, profesional_id: SimpleNamespace(prestacion_id=1),
    )
    recibido = {}
    monkeypatch.setattr(
        disponibilidades,
        "obtener_horarios_libres",
        lambda db, prestacion_id, fecha, turno_id_excluido: recibido.update(
            turno_id_excluido=turno_id_excluido,
        ) or [],
    )

    respuesta = client.get(
        "/disponibilidades/horarios-libres/",
        params={"prestacion_id": 1, "fecha": "2030-01-01", "turno_id_excluido": 25},
    )

    assert respuesta.status_code == 200
    assert recibido["turno_id_excluido"] == 25


def test_profesional_no_puede_excluir_turno_ajeno(
    client,
    usuarios,
    monkeypatch,
):
    autenticar_como(usuarios["profesional"])
    monkeypatch.setattr(disponibilidades, "obtener_mi_profesional", lambda *args: SimpleNamespace(id=10))
    monkeypatch.setattr(disponibilidades, "buscar_turno_de_profesional", lambda *args: None)

    respuesta = client.get(
        "/disponibilidades/horarios-libres/",
        params={"prestacion_id": 1, "fecha": "2030-01-01", "turno_id_excluido": 25},
    )

    assert respuesta.status_code == 404


def test_exclusion_de_turno_inexistente_devuelve_404(
    client,
    usuarios,
):
    autenticar_como(usuarios["administrador"])

    respuesta = client.get(
        "/disponibilidades/horarios-libres/",
        params={
            "prestacion_id": 1,
            "fecha": "2030-01-01",
            "turno_id_excluido": 999999,
        },
    )

    assert respuesta.status_code == 404
    assert respuesta.json() == {
        "detail": "Turno no encontrado."
    }


@pytest.mark.parametrize(
    "metodo,ruta,payload",
    [
        ("get", "/especialidades/", None),
        ("get", "/especialidades/1", None),
        (
            "post",
            "/especialidades/",
            {
                "nombre": "Clínica Médica",
                "duracion_turno_minutos": 30,
            },
        ),
        (
            "patch",
            "/especialidades/1",
            {"activa": False},
        ),
        ("get", "/disponibilidades/", None),
        ("get", "/disponibilidades/profesional/10", None),
        (
            "post",
            "/disponibilidades/",
            {
                "profesional_id": 10,
                "dia_semana": 0,
                "hora_inicio": "09:00:00",
                "hora_fin": "12:00:00",
            },
        ),
        (
            "get",
            "/disponibilidades/horarios-libres/"
            "?prestacion_id=1&fecha=2030-01-01",
            None,
        ),
    ],
)
def test_catalogo_y_disponibilidades_exigen_autenticacion(
    client,
    metodo,
    ruta,
    payload,
):
    respuesta = client.request(
        metodo.upper(),
        ruta,
        json=payload,
    )

    assert respuesta.status_code in {401, 403}
