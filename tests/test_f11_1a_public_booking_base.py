from uuid import UUID

from app.core.public_booking import es_slug_publico_valido
from app.models.especialidad import Especialidad
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from tests.conftest import SessionTest


def test_slug_publico_valida_formato():
    assert es_slug_publico_valido("dra-laura-gomez-k7m4")
    for slug in ("", "Dra-laura", "dra laura", "-invalido", "invalido-", "dos--guiones", "área", "dra_laura", "dra.laura"):
        assert not es_slug_publico_valido(slug)
    assert not es_slug_publico_valido("a" * 121)
    assert es_slug_publico_valido("a" * 120)


def test_campos_f11_1a_tienen_defaults_de_publicacion():
    profesional = Profesional.__table__.c
    prestacion = Prestacion.__table__.c
    assert profesional.reserva_online_activa.default.arg is False
    assert profesional.reserva_online_activa.nullable is False
    assert profesional.slug_publico.nullable is True
    assert prestacion.habilitada_online.default.arg is False
    assert prestacion.habilitada_online.nullable is False
    assert prestacion.identificador_publico.unique is True

    db = SessionTest()
    try:
        especialidad = Especialidad(
            nombre="F11 Especialidad",
            duracion_turno_minutos=30,
        )
        profesional = Profesional(
            nombre="Ana",
            apellido="Pérez",
            matricula="F11-1",
            especialidades_asignadas=[],
        )
        db.add_all([especialidad, profesional])
        db.flush()
        prestaciones = [
            Prestacion(
                nombre="Consulta A",
                duracion_minutos=30,
                precio=0,
                modalidad="presencial",
                profesional_id=profesional.id,
                especialidad_id=especialidad.id,
            ),
            Prestacion(
                nombre="Consulta B",
                duracion_minutos=45,
                precio=0,
                modalidad="virtual",
                profesional_id=profesional.id,
                especialidad_id=especialidad.id,
            ),
        ]
        db.add_all(prestaciones)
        db.commit()
        db.refresh(prestaciones[0])
        db.refresh(prestaciones[1])

        identificadores = [item.identificador_publico for item in prestaciones]
        assert all(item is not None for item in identificadores)
        assert all(UUID(item).version == 4 for item in identificadores)
        assert len(set(identificadores)) == 2

        identificador_original = prestaciones[0].identificador_publico
        prestaciones[0].nombre = "Consulta A actualizada"
        db.commit()
        db.refresh(prestaciones[0])
        assert prestaciones[0].identificador_publico == identificador_original
    finally:
        db.close()
