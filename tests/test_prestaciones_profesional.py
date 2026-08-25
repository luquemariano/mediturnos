from decimal import Decimal
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app.models.especialidad import Especialidad
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_especialidad import ProfesionalEspecialidad
from app.schemas.prestacion import PrestacionProfesionalCrear, PrestacionProfesionalActualizar
from app.services.prestacion_service import (crear_prestacion_profesional, desactivar_prestacion_profesional,
    modificar_prestacion_profesional, obtener_prestaciones_profesional)

def escenario(db):
    esp=Especialidad(nombre="Clínica")
    p1=Profesional(nombre="Sofía",apellido="Propia",matricula="PP1",activo=True)
    p2=Profesional(nombre="Martín",apellido="Ajeno",matricula="PP2",activo=True)
    db.add_all([esp,p1,p2]);db.flush();db.add_all([ProfesionalEspecialidad(profesional_id=p1.id,especialidad_id=esp.id),ProfesionalEspecialidad(profesional_id=p2.id,especialidad_id=esp.id)]);db.flush()
    a=Prestacion(nombre="Consulta",duracion_minutos=30,precio=Decimal("100"),modalidad="presencial",activa=True,profesional_id=p1.id,especialidad_id=esp.id)
    b=Prestacion(nombre="Ajena",duracion_minutos=45,precio=Decimal("200"),modalidad="virtual",activa=True,profesional_id=p2.id,especialidad_id=esp.id)
    db.add_all([a,b]);db.commit();return p1,p2,esp,a,b

def test_lista_crea_y_ordena_solo_propias():
    from tests.conftest import SessionTest
    db=SessionTest();p1,_,esp,a,_=escenario(db)
    creada=crear_prestacion_profesional(db,p1.id,PrestacionProfesionalCrear(nombre="Control",duracion_minutos=20,precio=0,especialidad_id=esp.id))
    assert {x.id for x in obtener_prestaciones_profesional(db,p1.id)}=={a.id,creada.id}
    assert creada.profesional_id==p1.id
    db.close()

def test_edicion_y_baja_respetan_ownership_y_no_borran():
    from tests.conftest import SessionTest
    db=SessionTest();p1,_,_,propia,ajena=escenario(db)
    original_fin="se conserva en Turno; la prestación no lo modifica"
    assert modificar_prestacion_profesional(db,p1.id,propia.id,PrestacionProfesionalActualizar(duracion_minutos=60)).duracion_minutos==60
    with pytest.raises(HTTPException) as error: modificar_prestacion_profesional(db,p1.id,ajena.id,PrestacionProfesionalActualizar(nombre="Intrusión"))
    assert error.value.status_code==404
    desactivar_prestacion_profesional(db,p1.id,propia.id)
    assert db.get(Prestacion,propia.id) is not None and not propia.activa and original_fin
    with pytest.raises(HTTPException) as error: desactivar_prestacion_profesional(db,p1.id,ajena.id)
    assert error.value.status_code==404
    db.close()

@pytest.mark.parametrize("campo,valor",[("duracion_minutos",0),("precio",-1)])
def test_valida_duracion_y_precio(campo,valor):
    datos=dict(nombre="Consulta",duracion_minutos=30,precio=0,especialidad_id=1);datos[campo]=valor
    with pytest.raises(ValidationError): PrestacionProfesionalCrear(**datos)

def test_no_acepta_profesional_id():
    with pytest.raises(ValidationError): PrestacionProfesionalCrear(nombre="Consulta",duracion_minutos=30,precio=0,especialidad_id=1,profesional_id=9)

def test_reactiva_propia_y_persiste_pero_no_reactiva_ajena():
    from tests.conftest import SessionTest
    db=SessionTest();p1,_,_,propia,ajena=escenario(db)
    propia.activa=False;ajena.activa=False;db.commit()
    respuesta=modificar_prestacion_profesional(db,p1.id,propia.id,PrestacionProfesionalActualizar(activa=True))
    assert respuesta.activa is True
    db.expire_all()
    assert db.get(Prestacion,propia.id).activa is True
    with pytest.raises(HTTPException) as error:
        modificar_prestacion_profesional(db,p1.id,ajena.id,PrestacionProfesionalActualizar(activa=True))
    assert error.value.status_code==404
    assert db.get(Prestacion,ajena.id).activa is False
    db.close()
