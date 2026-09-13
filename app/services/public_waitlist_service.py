from datetime import datetime, time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.paciente import Paciente
from app.models.profesional_paciente import ProfesionalPaciente
from app.repositories.public_booking_repository import (
    buscar_paciente_por_dni_publico,
    buscar_paciente_vinculado_por_email,
)
from app.schemas.public_booking import PublicWaitlistCreate
from app.schemas.waitlist import WaitlistEntryCreate
from app.services.public_booking_service import _profesional_y_prestacion_publicos
from app.services.waitlist_service import create_waitlist_entry


def _hora(valor: str | None) -> time | None:
    return datetime.strptime(valor, "%H:%M").time() if valor else None


def crear_entrada_waitlist_publica(db: Session, slug: str, datos: PublicWaitlistCreate):
    profesional, prestacion = _profesional_y_prestacion_publicos(db, slug, datos.prestacion)
    email = datos.paciente.email.strip().lower()
    dni = datos.paciente.dni.strip() if datos.paciente.dni and datos.paciente.dni.strip() else None
    paciente = buscar_paciente_por_dni_publico(db, dni) if dni else buscar_paciente_vinculado_por_email(db, profesional.id, email)

    try:
        if paciente is None:
            paciente = Paciente(
                nombre=datos.paciente.nombre.strip(),
                apellido=datos.paciente.apellido.strip(),
                email=email,
                telefono=datos.paciente.telefono.strip() if datos.paciente.telefono else None,
                dni=dni,
                activo=True,
            )
            db.add(paciente)
            db.flush()

        vinculo = db.query(ProfesionalPaciente).filter(
            ProfesionalPaciente.profesional_id == profesional.id,
            ProfesionalPaciente.paciente_id == paciente.id,
        ).first()
        if vinculo is None:
            db.add(ProfesionalPaciente(profesional_id=profesional.id, paciente_id=paciente.id, activo=True))
            db.flush()
        elif not vinculo.activo:
            vinculo.activo = True

        entrada = create_waitlist_entry(
            db,
            profesional.id,
            WaitlistEntryCreate(
                prestacion_id=prestacion.id,
                paciente_id=paciente.id,
                fecha_desde=datos.fecha_desde,
                fecha_hasta=datos.fecha_hasta,
                hora_desde=_hora(datos.hora_desde),
                hora_hasta=_hora(datos.hora_hasta),
            ),
            origen="publico",
        )
    except HTTPException as error:
        db.rollback()
        if error.status_code == 409:
            raise HTTPException(409, "No pudimos registrar tu solicitud.") from error
        raise
    except Exception:
        db.rollback()
        raise

    return {"message": "Te sumamos a la lista de espera. Te avisaremos por email si aparece un horario compatible."}
