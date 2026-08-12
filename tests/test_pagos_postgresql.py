import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier, Lock

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.models.usuario import Usuario
from app.services import pago_service


POSTGRES_URL = os.getenv("TEST_POSTGRES_PAYMENTS_URL")

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason=(
        "Requiere PostgreSQL real mediante "
        "TEST_POSTGRES_PAYMENTS_URL."
    ),
)

engine_postgresql = (
    create_engine(POSTGRES_URL, pool_size=8)
    if POSTGRES_URL
    else None
)
SessionPostgresql = (
    sessionmaker(
        bind=engine_postgresql,
        expire_on_commit=False,
    )
    if engine_postgresql is not None
    else None
)


class PreferenciasConcurrentes:
    def __init__(self):
        self.cantidad = 0
        self._lock = Lock()

    def create(self, _datos):
        with self._lock:
            self.cantidad += 1

        return {
            "status": 201,
            "response": {
                "id": "pref-concurrente",
                "init_point": "https://example.com/pagar",
            },
        }


class SDKPreferencia:
    def __init__(self, recurso):
        self.recurso = recurso

    def preference(self):
        return self.recurso


class SDKWebhook:
    def __init__(self, datos_pago):
        self.datos_pago = datos_pago

    def payment(self):
        datos = self.datos_pago

        class Recurso:
            def get(self, _payment_id):
                return {"status": 200, "response": datos}

        return Recurso()

    def merchant_order(self):
        class Recurso:
            def get(self, _order_id):
                return {
                    "status": 200,
                    "response": {
                        "preference_id": "pref-webhook-pg"
                    },
                }

        return Recurso()


@pytest.fixture
def escenario_postgresql(monkeypatch):
    with engine_postgresql.begin() as conexion:
        conexion.execute(
            text(
                "TRUNCATE TABLE pagos, turnos, disponibilidades, "
                "prestaciones, profesionales_especialidades, "
                "pacientes, profesionales, especialidades, "
                "usuarios RESTART IDENTITY CASCADE"
            )
        )

    with SessionPostgresql() as db:
        pacientes = [
            Paciente(
                nombre=f"Paciente {numero}",
                apellido="Pagos PG",
                dni=f"3011199{numero}",
                telefono="3515550000",
            )
            for numero in (1, 2)
        ]
        profesional = Profesional(
            nombre="Profesional",
            apellido="Pagos PG",
            matricula="MP-PAGOS-PG-001",
        )
        especialidad = Especialidad(
            nombre="Especialidad pagos PG",
            duracion_turno_minutos=30,
        )
        db.add_all([*pacientes, profesional, especialidad])
        db.flush()
        prestacion = Prestacion(
            nombre="Consulta pagos PG",
            duracion_minutos=30,
            precio=Decimal("15000.00"),
            modalidad="presencial",
            profesional_id=profesional.id,
            especialidad_id=especialidad.id,
        )
        db.add(prestacion)
        db.flush()
        inicio = datetime.now(UTC) + timedelta(days=7)
        turno = Turno(
            paciente_id=pacientes[0].id,
            prestacion_id=prestacion.id,
            profesional_id=profesional.id,
            fecha_hora=inicio,
            fecha_fin=inicio + timedelta(minutes=30),
        )
        db.add(turno)
        db.commit()
        escenario = {
            "pacientes": [paciente.id for paciente in pacientes],
            "profesional_id": profesional.id,
            "prestacion_id": prestacion.id,
            "turno_id": turno.id,
            "inicio": inicio,
        }

    monkeypatch.setattr(
        settings,
        "mercado_pago_access_token",
        "token-test",
    )
    yield escenario

    with engine_postgresql.begin() as conexion:
        conexion.execute(
            text(
                "TRUNCATE TABLE pagos, turnos, disponibilidades, "
                "prestaciones, profesionales_especialidades, "
                "pacientes, profesionales, especialidades, "
                "usuarios RESTART IDENTITY CASCADE"
            )
        )


def administrador():
    return Usuario(
        nombre="Admin",
        email="admin-concurrencia@example.com",
        password_hash="hash",
        rol="administrador",
    )


def test_dos_preferencias_concurrentes_crean_un_solo_pago(
    escenario_postgresql,
    monkeypatch,
):
    barrera = Barrier(2, timeout=10)
    bloquear_original = pago_service.bloquear_turno_para_pago

    def sincronizar_y_bloquear(*args, **kwargs):
        barrera.wait()
        return bloquear_original(*args, **kwargs)

    monkeypatch.setattr(
        pago_service,
        "bloquear_turno_para_pago",
        sincronizar_y_bloquear,
    )
    recurso = PreferenciasConcurrentes()
    monkeypatch.setattr(
        pago_service.mercadopago,
        "SDK",
        lambda _token: SDKPreferencia(recurso),
    )

    def crear():
        with SessionPostgresql() as db:
            pago = pago_service.crear_preferencia_pago(
                db,
                escenario_postgresql["turno_id"],
                administrador(),
            )
            return pago.id, pago.preference_id

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = [
            futuro.result()
            for futuro in [
                ejecutor.submit(crear),
                ejecutor.submit(crear),
            ]
        ]

    assert resultados[0] == resultados[1]
    assert recurso.cantidad == 1

    with SessionPostgresql() as db:
        assert db.query(Pago).count() == 1


def test_webhook_aprobado_con_horario_reutilizado(
    escenario_postgresql,
    monkeypatch,
):
    with SessionPostgresql() as db:
        turno_cancelado = db.get(
            Turno,
            escenario_postgresql["turno_id"],
        )
        turno_cancelado.estado = "cancelado"
        turno_reemplazo = Turno(
            paciente_id=escenario_postgresql["pacientes"][1],
            prestacion_id=escenario_postgresql["prestacion_id"],
            profesional_id=escenario_postgresql["profesional_id"],
            fecha_hora=escenario_postgresql["inicio"],
            fecha_fin=(
                escenario_postgresql["inicio"]
                + timedelta(minutes=30)
            ),
        )
        db.add(turno_reemplazo)
        db.flush()
        pago = Pago(
            turno_id=turno_cancelado.id,
            preference_id="pref-webhook-pg",
            estado="pendiente",
            monto=Decimal("15000.00"),
            init_point="https://example.com/pagar",
        )
        db.add(pago)
        db.commit()
        pago_id = pago.id
        turno_reemplazo_id = turno_reemplazo.id

    datos = {
        "id": "payment-webhook-pg",
        "status": "approved",
        "external_reference": str(
            escenario_postgresql["turno_id"]
        ),
        "transaction_amount": "15000.00",
        "currency_id": "ARS",
        "date_last_updated": "2026-08-12T15:00:00+00:00",
        "metadata": {
            "pago_id": pago_id,
            "turno_id": escenario_postgresql["turno_id"],
        },
        "order": {"id": "merchant-order-pg"},
    }
    monkeypatch.setattr(
        pago_service.mercadopago,
        "SDK",
        lambda _token: SDKWebhook(datos),
    )

    with SessionPostgresql() as db:
        rollback_original = db.rollback
        rollbacks = 0

        def registrar_rollback():
            nonlocal rollbacks
            rollbacks += 1
            rollback_original()

        monkeypatch.setattr(db, "rollback", registrar_rollback)
        pago = pago_service.procesar_notificacion_pago(
            db,
            "payment-webhook-pg",
        )

        assert pago.estado == "approved"
        assert pago.requiere_revision is True
        assert pago.motivo_revision == "horario_reutilizado"
        assert pago.turno.estado == "cancelado"
        assert rollbacks == 1
        assert db.execute(select(1)).scalar_one() == 1

    with SessionPostgresql() as db:
        assert db.get(Turno, turno_reemplazo_id).estado == (
            "reservado"
        )
        assert db.query(Pago).count() == 1


def test_fallo_segundo_commit_hace_rollback_y_permite_reintento(
    escenario_postgresql,
    monkeypatch,
):
    with SessionPostgresql() as db:
        turno_cancelado = db.get(
            Turno,
            escenario_postgresql["turno_id"],
        )
        turno_cancelado.estado = "cancelado"
        turno_reemplazo = Turno(
            paciente_id=escenario_postgresql["pacientes"][1],
            prestacion_id=escenario_postgresql["prestacion_id"],
            profesional_id=escenario_postgresql["profesional_id"],
            fecha_hora=escenario_postgresql["inicio"],
            fecha_fin=(
                escenario_postgresql["inicio"]
                + timedelta(minutes=30)
            ),
        )
        db.add(turno_reemplazo)
        db.flush()
        pago = Pago(
            turno_id=turno_cancelado.id,
            preference_id="pref-webhook-pg",
            estado="pendiente",
            monto=Decimal("15000.00"),
            init_point="https://example.com/pagar",
        )
        db.add(pago)
        db.commit()
        pago_id = pago.id

    datos = {
        "id": "payment-webhook-pg",
        "status": "approved",
        "external_reference": str(
            escenario_postgresql["turno_id"]
        ),
        "transaction_amount": "15000.00",
        "currency_id": "ARS",
        "date_last_updated": "2026-08-12T15:00:00+00:00",
        "metadata": {
            "pago_id": pago_id,
            "turno_id": escenario_postgresql["turno_id"],
        },
        "order": {"id": "merchant-order-pg"},
    }
    monkeypatch.setattr(
        pago_service.mercadopago,
        "SDK",
        lambda _token: SDKWebhook(datos),
    )

    with SessionPostgresql() as db:
        commit_original = db.commit
        rollback_original = db.rollback
        commits = 0
        rollbacks = 0

        def commit_controlado():
            nonlocal commits
            commits += 1

            if commits == 2:
                raise RuntimeError("fallo del segundo commit")

            commit_original()

        def rollback_controlado():
            nonlocal rollbacks
            rollbacks += 1
            rollback_original()

        monkeypatch.setattr(db, "commit", commit_controlado)
        monkeypatch.setattr(db, "rollback", rollback_controlado)

        with pytest.raises(
            RuntimeError,
            match="fallo del segundo commit",
        ):
            pago_service.procesar_notificacion_pago(
                db,
                "payment-webhook-pg",
            )

        assert commits == 2
        assert rollbacks == 2
        assert db.execute(select(1)).scalar_one() == 1

    with SessionPostgresql() as db:
        pago = db.get(Pago, pago_id)
        turno = db.get(
            Turno,
            escenario_postgresql["turno_id"],
        )
        assert pago.estado == "pendiente"
        assert pago.payment_id is None
        assert pago.requiere_revision is False
        assert pago.motivo_revision is None
        assert turno.estado == "cancelado"

        reintentado = pago_service.procesar_notificacion_pago(
            db,
            "payment-webhook-pg",
        )

        assert reintentado.estado == "approved"
        assert reintentado.requiere_revision is True
        assert reintentado.motivo_revision == (
            "horario_reutilizado"
        )
        assert reintentado.turno.estado == "cancelado"
