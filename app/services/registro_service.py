from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.jwt import crear_access_token
from app.core.security import generar_hash_password
from app.models.profesional import Profesional
from app.models.profesional_especialidad import ProfesionalEspecialidad
from app.models.usuario import Usuario
from app.repositories.especialidad_repository import buscar_por_id
from app.repositories.usuario_repository import buscar_usuario_por_email
from app.schemas.auth import RegistroProfesionalDatos, RegistroProfesionalRespuesta


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def registrar_profesional_publico(
    db: Session, datos: RegistroProfesionalDatos,
) -> RegistroProfesionalRespuesta:
    email = normalizar_email(str(datos.email))
    if buscar_usuario_por_email(db, email) is not None:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese email.")

    especialidad = buscar_por_id(db, datos.especialidad_id)
    if especialidad is None or not especialidad.activa:
        raise HTTPException(status_code=400, detail="La especialidad seleccionada no está disponible.")

    usuario = Usuario(
        nombre=f"{datos.nombre.strip()} {datos.apellido.strip()}",
        email=email,
        password_hash=generar_hash_password(datos.password),
        rol="profesional",
    )
    profesional = Profesional(
        usuario=usuario,
        nombre=datos.nombre.strip(),
        apellido=datos.apellido.strip(),
        matricula=datos.matricula.strip(),
        telefono=datos.telefono.strip() if datos.telefono else None,
        email=email,
        onboarding_step="perfil",
    )
    profesional.especialidades_asignadas.append(
        ProfesionalEspecialidad(
            especialidad=especialidad,
            duracion_turno_minutos=especialidad.duracion_turno_minutos,
        )
    )
    db.add(profesional)
    try:
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

    token = crear_access_token(usuario.id, usuario.email, usuario.rol)
    return RegistroProfesionalRespuesta(
        access_token=token,
        usuario_id=usuario.id,
        usuario=usuario.nombre,
        rol=usuario.rol,
        profesional_id=profesional.id,
        onboarding_step=profesional.onboarding_step,
    )
