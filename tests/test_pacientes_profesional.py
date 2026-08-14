from datetime import datetime, timezone

from app.models.paciente import Paciente
from app.models.profesional import Profesional
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.turno import Turno
from app.models.prestacion import Prestacion
from app.models.especialidad import Especialidad
from app.services.paciente_service import (
    actualizar_paciente_profesional, crear_paciente_profesional,
    desactivar_paciente_profesional, obtener_pacientes_profesional,
    obtener_turnos_paciente_profesional,
)
from app.schemas.paciente import PacienteProfesionalCrear, PacienteProfesionalActualizar
from fastapi import HTTPException
import pytest


def preparar(db):
    p1=Profesional(nombre="Uno",apellido="Propio",matricula="M1",activo=True)
    p2=Profesional(nombre="Dos",apellido="Ajeno",matricula="M2",activo=True)
    a=Paciente(nombre="Ana",apellido="Propia",dni="11111111",telefono="111111",activo=True)
    b=Paciente(nombre="Berta",apellido="Ajena",dni="22222222",telefono="222222",activo=True)
    db.add_all([p1,p2,a,b]); db.flush()
    db.add_all([ProfesionalPaciente(profesional_id=p1.id,paciente_id=a.id),ProfesionalPaciente(profesional_id=p2.id,paciente_id=b.id)]); db.commit()
    return p1,p2,a,b

def test_lista_y_busqueda_solo_propios():
    from tests.conftest import SessionTest
    db=SessionTest(); p1,_,a,b=preparar(db)
    assert obtener_pacientes_profesional(db,p1.id)==[a]
    assert obtener_pacientes_profesional(db,p1.id,"Berta")==[]
    assert obtener_pacientes_profesional(db,p1.id,"Ana")==[a]
    db.close()

def test_crud_respeta_vinculo_y_soft_delete():
    from tests.conftest import SessionTest
    db=SessionTest(); p1,_,propio,ajeno=preparar(db)
    creado=crear_paciente_profesional(db,p1.id,PacienteProfesionalCrear(nombre="Carlos",apellido="Nuevo"))
    assert creado.dni is None
    actualizado=actualizar_paciente_profesional(db,p1.id,creado.id,PacienteProfesionalActualizar(telefono="123456"))
    assert actualizado.telefono=="123456"
    with pytest.raises(HTTPException) as error: actualizar_paciente_profesional(db,p1.id,ajeno.id,PacienteProfesionalActualizar(nombre="Intrusión"))
    assert error.value.status_code==404
    desactivar_paciente_profesional(db,p1.id,creado.id)
    assert obtener_pacientes_profesional(db,p1.id)==[propio]
    assert db.get(Paciente,creado.id) is not None
    db.close()

def test_historial_ajeno_no_se_filtra():
    from tests.conftest import SessionTest
    db=SessionTest(); p1,_,_,ajeno=preparar(db)
    with pytest.raises(HTTPException) as error: obtener_turnos_paciente_profesional(db,p1.id,ajeno.id)
    assert error.value.status_code==404
    db.close()
