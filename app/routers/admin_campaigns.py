import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import update

from app.core.dependencies import requiere_administrador
from app.database.connection import obtener_db
from app.models.campania_novedades import CampaniaNovedades, EntregaCampaniaNovedades, NovedadProducto
from app.models.usuario import Usuario
from app.models.profesional import Profesional
from app.schemas.campaign import CampaniaEntrada, ConfirmarEnvio, NovedadEntrada, NovedadRespuesta
from app.schemas.campaign import TokenBajaEntrada
from app.services.campaign_service import baja, contenido_email, destinatarios, ejecutar_envio, serializar_novedad, verificar_token_baja
from app.services.engagement_email_service import construir_email_engagement

router = APIRouter(prefix="/admin/campanias", tags=["Campañas"], dependencies=[Depends(requiere_administrador)])
public_router = APIRouter(prefix="/public/baja-novedades", tags=["Baja de novedades"])


@router.get("/novedades", response_model=list[NovedadRespuesta])
def listar_novedades(db: Session = Depends(obtener_db)):
    return db.query(NovedadProducto).order_by(NovedadProducto.activa.desc(), NovedadProducto.id.desc()).all()


@router.post("/novedades", response_model=NovedadRespuesta, status_code=201)
def crear_novedad(datos: NovedadEntrada, db: Session = Depends(obtener_db)):
    item = NovedadProducto(**datos.model_dump()); db.add(item); db.commit(); db.refresh(item); return item


@router.put("/novedades/{novedad_id}", response_model=NovedadRespuesta)
def actualizar_novedad(novedad_id: int, datos: NovedadEntrada, db: Session = Depends(obtener_db)):
    item = db.get(NovedadProducto, novedad_id)
    if not item: raise HTTPException(404, "Novedad inexistente.")
    for key, value in datos.model_dump().items(): setattr(item, key, value)
    item.actualizado_en = datetime.now(timezone.utc); db.commit(); db.refresh(item); return item


@router.delete("/novedades/{novedad_id}", status_code=204)
def eliminar_novedad(novedad_id: int, db: Session = Depends(obtener_db)):
    item = db.get(NovedadProducto, novedad_id)
    if not item: raise HTTPException(404, "Novedad inexistente.")
    db.delete(item); db.commit()


@router.get("/destinatarios")
def listar_destinatarios(busqueda: str | None = Query(default=None, max_length=120), db: Session = Depends(obtener_db)):
    rows = db.query(Usuario.id, Usuario.nombre, Usuario.email).join(Profesional, Profesional.usuario_id == Usuario.id).filter(Usuario.rol == "profesional", Usuario.activo.is_(True), Profesional.activo.is_(True), Usuario.fecha_baja_novedades.is_(None))
    if busqueda:
        from sqlalchemy import or_
        patron = f"%{busqueda.strip()}%"
        rows = rows.filter(or_(Usuario.nombre.ilike(patron), Usuario.email.ilike(patron), Profesional.nombre.ilike(patron), Profesional.apellido.ilike(patron)))
    return [{"id": id_, "nombre": nombre, "email": email} for id_, nombre, email in rows.order_by(Usuario.nombre, Usuario.id).all()]


def preparar(db: Session, actor: Usuario, datos: CampaniaEntrada) -> tuple[CampaniaNovedades, list[Usuario], list[NovedadProducto]]:
    existente = db.query(CampaniaNovedades).filter_by(idempotency_key=datos.idempotency_key).first()
    if existente: raise HTTPException(409, "La clave de idempotencia ya fue utilizada.")
    novedades = db.query(NovedadProducto).filter(NovedadProducto.id.in_(datos.novedades_ids), NovedadProducto.activa.is_(True), NovedadProducto.cerrada.is_(True)).all() if datos.novedades_ids else []
    if len(novedades) != len(set(datos.novedades_ids)): raise HTTPException(422, "Elegí novedades cerradas y activas.")
    disponibles = destinatarios(db)
    usuarios = disponibles if datos.todos else [u for u in disponibles if u.id in set(datos.destinatarios_ids)]
    if not datos.todos and len(usuarios) != len(set(datos.destinatarios_ids)): raise HTTPException(422, "La selección contiene destinatarios no disponibles.")
    campania = CampaniaNovedades(asunto=datos.asunto, preheader=datos.preheader, mensaje_principal=datos.mensaje_principal,
        novedades_json=json.dumps([serializar_novedad(n) for n in novedades]), creada_por=actor.id,
        destinatarios_json=json.dumps([u.id for u in usuarios]), fecha_creacion=datetime.now(timezone.utc), idempotency_key=datos.idempotency_key)
    return campania, usuarios, novedades


@router.post("/preview")
def preview(datos: CampaniaEntrada, db: Session = Depends(obtener_db)):
    novedades = db.query(NovedadProducto).filter(NovedadProducto.id.in_(datos.novedades_ids), NovedadProducto.activa.is_(True), NovedadProducto.cerrada.is_(True)).all() if datos.novedades_ids else []
    if len(novedades) != len(set(datos.novedades_ids)): raise HTTPException(422, "Elegí novedades cerradas y activas.")
    disponibles = destinatarios(db)
    usuarios = disponibles if datos.todos else [u for u in disponibles if u.id in set(datos.destinatarios_ids)]
    if not datos.todos and len(usuarios) != len(set(datos.destinatarios_ids)): raise HTTPException(422, "La selección contiene destinatarios no disponibles.")
    dummy = usuarios[0] if usuarios else Usuario(id=0, nombre="Profesional", email="profesional@example.test")
    contenido = [serializar_novedad(novedad) for novedad in novedades]
    email = construir_email_engagement(contenido_email(datos.asunto, datos.preheader, datos.mensaje_principal, contenido, dummy, "preview-token"))
    return {"asunto": email.asunto, "html": email.html, "texto": email.texto, "destinatarios": len(usuarios)}


@router.post("", status_code=201)
def crear_campania(datos: CampaniaEntrada, actor: Usuario = Depends(requiere_administrador), db: Session = Depends(obtener_db)):
    campania, _, _ = preparar(db, actor, datos); db.add(campania); db.commit(); db.refresh(campania); return {"id": campania.id, "fecha_creacion": campania.fecha_creacion}


@router.get("")
def listar_campanias(db: Session = Depends(obtener_db)):
    return [{"id": c.id, "asunto": c.asunto, "fecha_creacion": c.fecha_creacion, "entregas": db.query(EntregaCampaniaNovedades).filter_by(campania_id=c.id).count()} for c in db.query(CampaniaNovedades).order_by(CampaniaNovedades.id.desc()).all()]


@router.get("/{campania_id}")
def detalle_campania(campania_id: int, db: Session = Depends(obtener_db)):
    c = db.get(CampaniaNovedades, campania_id)
    if not c: raise HTTPException(404, "Campaña inexistente.")
    e = db.query(EntregaCampaniaNovedades).filter_by(campania_id=c.id).all()
    return {"id": c.id, "asunto": c.asunto, "preheader": c.preheader, "mensaje_principal": c.mensaje_principal, "novedades": json.loads(c.novedades_json), "fecha_creacion": c.fecha_creacion, "entregas": [{"email": x.email, "estado": x.estado, "provider": x.provider, "message_id": x.message_id, "error": x.error, "fecha": x.fecha} for x in e]}


@router.post("/{campania_id}/enviar")
def enviar_campania(campania_id: int, confirmacion: ConfirmarEnvio, actor: Usuario = Depends(requiere_administrador), db: Session = Depends(obtener_db)):
    c = db.get(CampaniaNovedades, campania_id)
    if not c: raise HTTPException(404, "Campaña inexistente.")
    reclamada = db.execute(update(CampaniaNovedades).where(CampaniaNovedades.id == c.id, CampaniaNovedades.envio_iniciado.is_(False)).values(envio_iniciado=True))
    if reclamada.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "El envío de esta campaña ya fue iniciado.")
    db.commit()
    ids = json.loads(c.destinatarios_json)
    usuarios = db.query(Usuario).filter(Usuario.id.in_(ids)).all() if ids else []
    return ejecutar_envio(db, c, usuarios)


@public_router.post("")
def ejecutar_baja(datos: TokenBajaEntrada, db: Session = Depends(obtener_db)):
    usuario_id = verificar_token_baja(datos.token)
    baja(db, usuario_id)
    return {"baja_realizada": True}
