from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import generar_hash_password
from app.models.profesional import Profesional
from app.models.usuario import Usuario
from app.models.profesional_especialidad import ProfesionalEspecialidad
from app.services.cuenta_service import crear_cuenta_individual_con_trial
from app.repositories.usuario_repository import buscar_usuario_por_email
from app.schemas.auth import RegistroProfesionalDatos, RegistroProfesionalRespuesta
from app.services.email_verification_service import generar_token_verificacion
from app.services.email_service import EmailDeliveryError, enviar_verificacion_email
from app.services.actividad_profesional_service import validar_datos_de_actividad
from app.repositories.profesional_repository import buscar_especialidades_por_ids


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def registrar_profesional_publico(
    db: Session, datos: RegistroProfesionalDatos,
) -> RegistroProfesionalRespuesta:
    email = normalizar_email(str(datos.email))
    if buscar_usuario_por_email(db, email) is not None:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese email.")

    actividad, especialidad_ids = validar_datos_de_actividad(
        db,
        datos.actividad_profesional_id,
        datos.matricula,
        None,
        datos.especialidad_id,
    )
    especialidades = buscar_especialidades_por_ids(db, especialidad_ids)
    por_id = {item.id: item for item in especialidades if item.activa}
    if set(por_id) != set(especialidad_ids):
        raise HTTPException(status_code=400, detail="La especialidad seleccionada no está disponible.")

    usuario = Usuario(
        nombre=f"{datos.nombre.strip()} {datos.apellido.strip()}",
        email=email,
        password_hash=generar_hash_password(datos.password),
        rol="profesional",
    )
    try:
        cuenta = crear_cuenta_individual_con_trial(usuario.nombre, usuario)
    except Exception:
        db.rollback()
        raise
    profesional = Profesional(
        usuario=usuario,
        cuenta=cuenta,
        nombre=datos.nombre.strip(),
        apellido=datos.apellido.strip(),
        matricula=datos.matricula.strip() if datos.matricula else None,
        actividad_profesional=actividad,
        telefono=datos.telefono.strip() if datos.telefono else None,
        email=email,
        onboarding_step="perfil",
    )
    for especialidad in especialidades:
        profesional.especialidades_asignadas.append(
            ProfesionalEspecialidad(
                especialidad=especialidad,
                duracion_turno_minutos=especialidad.duracion_turno_minutos,
            )
        )
    db.add(profesional)
    try:
        db.flush()
        token = generar_token_verificacion(db, usuario)
        enviar_verificacion_email(usuario.email, usuario.nombre, token)
        db.commit()
        db.refresh(usuario)
        db.refresh(profesional)
    except IntegrityError as error:
        db.rollback()
        mensaje = str(getattr(error, "orig", "")).lower()
        if "matricula" in mensaje:
            detalle = "Ya existe un profesional con esa matrícula."
        else:
            detalle = "Ya existe una cuenta con ese email."
        raise HTTPException(status_code=409, detail=detalle) from None
    except EmailDeliveryError as error:
        db.rollback()
        raise HTTPException(status_code=503, detail="No pudimos enviar el correo de verificación. Intentá nuevamente.") from error

    return RegistroProfesionalRespuesta(
        mensaje="Cuenta creada. Revisá tu correo para verificarla antes de iniciar sesión.",
        usuario_id=usuario.id,
        usuario=usuario.nombre,
        rol=usuario.rol,
        profesional_id=profesional.id,
        onboarding_step=profesional.onboarding_step,
    )
