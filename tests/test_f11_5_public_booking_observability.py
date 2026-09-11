from datetime import datetime, time
from zoneinfo import ZoneInfo
from starlette.requests import Request
from tests.conftest import SessionTest
from app.models.disponibilidad import Disponibilidad
from tests.test_f11_1d_public_booking_availability import escenario, consultar
from app.core.rate_limit import obtener_ip_cliente

ZONA=ZoneInfo("America/Argentina/Buenos_Aires")

def test_disponibilidad_60_61_y_bucket_creacion_independiente(client, monkeypatch, caplog):
    db=SessionTest(); profesional, _, prestacion, _=escenario(db); monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,10,8,tzinfo=ZONA)); db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=3,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    for _ in range(60): assert consultar(client,profesional,prestacion,datetime(2026,9,10).date()).status_code==200
    blocked=consultar(client,profesional,prestacion,datetime(2026,9,10).date()); assert blocked.status_code==429; assert "public_disponibilidad" in caplog.text; assert "127.0.0.1" not in caplog.text
    body={"prestacion":prestacion.identificador_publico,"fecha_hora":"2026-09-10T10:00:00-03:00","paciente":{"nombre":"Ana","apellido":"Nueva","email":"observabilidad@example.com"}}
    assert client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=body).status_code==201
    db.close()

def test_trust_proxy_headers_ignorado_habilitado_y_malformado(monkeypatch):
    request=Request({"type":"http","client":("10.0.0.9",1234),"headers":[(b"x-forwarded-for",b"203.0.113.8, 10.0.0.9")]})
    monkeypatch.setattr("app.core.rate_limit.settings.trust_proxy_headers",False); assert obtener_ip_cliente(request)=="10.0.0.9"
    monkeypatch.setattr("app.core.rate_limit.settings.trust_proxy_headers",True); assert obtener_ip_cliente(request)=="203.0.113.8"
    request=Request({"type":"http","client":("10.0.0.9",1234),"headers":[(b"x-forwarded-for",b"not-an-ip")]}); assert obtener_ip_cliente(request)=="10.0.0.9"
