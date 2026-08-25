import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import ProfesionalShell from "./ProfesionalShell";
import "./MisPrestaciones.css";
import "./MisPrestacionesEstados.css";
import type { Prestacion, ModalidadPrestacion } from "../types/prestacion";
import type { Especialidad } from "../types/especialidad";
import { crearMiPrestacion, desactivarMiPrestacion, editarMiPrestacion, obtenerMisPrestaciones } from "../services/prestacionService";
import { obtenerEspecialidades } from "../services/especialidadService";
import { obtenerMiPerfilProfesional } from "../services/profesionalService";

type Props={nombre:string;onVolver:()=>void;onAbrirAgenda:()=>void;onAbrirPacientes:()=>void;onAbrirDisponibilidad:()=>void;onAbrirPerfil:()=>void;onCerrarSesion:()=>void};
const VACIO={nombre:"",duracion_minutos:"30",precio:"0",modalidad:"presencial" as ModalidadPrestacion,especialidad_id:""};
const errorDetalle=(e:unknown)=>axios.isAxiosError(e)&&typeof e.response?.data?.detail==="string"?e.response.data.detail:"Ocurrió un error inesperado.";
const precio=(valor:number|string)=>new Intl.NumberFormat("es-AR",{style:"currency",currency:"ARS"}).format(Number(valor));

export default function MisPrestaciones(props:Props){
  const [items,setItems]=useState<Prestacion[]>([]),[especialidades,setEspecialidades]=useState<Especialidad[]>([]),[cargando,setCargando]=useState(true);
  const [error,setError]=useState(""),[exito,setExito]=useState(""),[modal,setModal]=useState(false),[confirmar,setConfirmar]=useState(false),[guardando,setGuardando]=useState(false);
  const [reactivando,setReactivando]=useState(false);
  const [seleccion,setSeleccion]=useState<Prestacion|null>(null),[form,setForm]=useState(VACIO);
  const cargar=useCallback(async()=>{setCargando(true);setError("");try{const [prestaciones,perfil,catalogo]=await Promise.all([obtenerMisPrestaciones(),obtenerMiPerfilProfesional(),obtenerEspecialidades()]);const ids=new Set(perfil.especialidades.map(e=>e.especialidad_id));setItems(prestaciones);setEspecialidades(catalogo.filter(e=>ids.has(e.id)));}catch(e){setError(errorDetalle(e));}finally{setCargando(false)}},[]);
  useEffect(()=>{void cargar()},[cargar]);
  function nueva(){setSeleccion(null);setForm({...VACIO,especialidad_id:String(especialidades[0]?.id??"")});setModal(true);setExito("")}
  function gestionar(p:Prestacion){setSeleccion(p);setForm({nombre:p.nombre,duracion_minutos:String(p.duracion_minutos),precio:String(p.precio),modalidad:p.modalidad,especialidad_id:String(p.especialidad_id)});setModal(true);setExito("")}
  async function guardar(e:FormEvent){e.preventDefault();if(guardando)return;setGuardando(true);setError("");try{const datos={nombre:form.nombre,duracion_minutos:Number(form.duracion_minutos),precio:Number(form.precio),modalidad:form.modalidad,especialidad_id:Number(form.especialidad_id)};if(seleccion){await editarMiPrestacion(seleccion.id,{nombre:datos.nombre,duracion_minutos:datos.duracion_minutos,precio:datos.precio,modalidad:datos.modalidad});setExito("Prestación actualizada correctamente.");}else{await crearMiPrestacion(datos);setExito("Prestación creada correctamente.");}setModal(false);await cargar();}catch(e){setError(errorDetalle(e));}finally{setGuardando(false)}}
  async function desactivar(){if(!seleccion)return;try{await desactivarMiPrestacion(seleccion.id);setConfirmar(false);setModal(false);setExito("Prestación desactivada correctamente.");await cargar();}catch(e){setError(errorDetalle(e))}}
  async function reactivar(){
    if(!seleccion||reactivando)return;
    setReactivando(true);setError("");
    try{
      const actualizada=await editarMiPrestacion(seleccion.id,{activa:true});
      if(actualizada.activa!==true)throw new Error("La prestación no fue reactivada.");
      setItems(anteriores=>anteriores.map(item=>item.id===actualizada.id?actualizada:item));
      setSeleccion(actualizada);setModal(false);setExito("Prestación reactivada correctamente.");
    }catch(e){setError(errorDetalle(e));}
    finally{setReactivando(false)}
  }
  return <ProfesionalShell activo="prestaciones" nombre={props.nombre} tituloTopbar="Mis prestaciones" onAbrirInicio={props.onVolver} onAbrirAgenda={props.onAbrirAgenda} onAbrirPacientes={props.onAbrirPacientes} onAbrirDisponibilidad={props.onAbrirDisponibilidad} onAbrirPrestaciones={()=>undefined} onAbrirPerfil={props.onAbrirPerfil} onCerrarSesion={props.onCerrarSesion}>
    <div className="mis-prestaciones"><header><div><span>Servicios profesionales</span><h1>Mis prestaciones</h1><p>Definí los servicios disponibles para nuevas reservas.</p></div><button className="mp-boton primario" onClick={nueva}>Nueva prestación</button></header>
    {exito&&<p className="mp-feedback exito" role="status">{exito}</p>}{error&&<div className="mp-feedback error" role="alert"><span>{error}</span><button onClick={()=>void cargar()}>Reintentar</button></div>}
    {cargando?<div className="mp-estado">Cargando prestaciones...</div>:items.length===0?<div className="mp-estado"><h2>No tenés prestaciones registradas</h2><p>Creá la primera para habilitar nuevas reservas.</p></div>:<ul>{items.map(p=><li key={p.id}><div><strong>{p.nombre}</strong><span>{p.modalidad==="virtual"?"Virtual":"Presencial"}</span></div><dl><div><dt>Duración</dt><dd>{p.duracion_minutos} min</dd></div><div><dt>Precio</dt><dd>{precio(p.precio)}</dd></div><div><dt>Estado</dt><dd className={p.activa?"activa":"inactiva"}>{p.activa?"Activa":"Inactiva"}</dd></div></dl><button className="mp-boton secundario" onClick={()=>gestionar(p)}>Gestionar</button></li>)}</ul>}
    </div>
    {modal&&<div className="mp-overlay" role="dialog" aria-modal="true"><form className="mp-modal" onSubmit={guardar}><header><div><span>Prestación profesional</span><h2>{seleccion?"Gestionar prestación":"Nueva prestación"}</h2></div><button type="button" aria-label="Cerrar" onClick={()=>setModal(false)}>×</button></header><div className="mp-form"><label>Nombre *<input required minLength={2} value={form.nombre} onChange={e=>setForm({...form,nombre:e.target.value})}/></label><label>Duración *<input required type="number" min="10" max="240" value={form.duracion_minutos} onChange={e=>setForm({...form,duracion_minutos:e.target.value})}/></label><label>Precio<input type="number" min="0" step="0.01" value={form.precio} onChange={e=>setForm({...form,precio:e.target.value})}/></label><label>Modalidad<select value={form.modalidad} onChange={e=>setForm({...form,modalidad:e.target.value as ModalidadPrestacion})}><option value="presencial">Presencial</option><option value="virtual">Virtual</option></select></label><label>Especialidad<select required disabled={Boolean(seleccion)} value={form.especialidad_id} onChange={e=>setForm({...form,especialidad_id:e.target.value})}>{especialidades.map(x=><option key={x.id} value={x.id}>{x.nombre}</option>)}</select></label>{seleccion&&<p className="mp-aviso">Este cambio se aplicará a nuevas reservas. Los turnos ya creados conservarán su horario actual.</p>}</div><footer>{seleccion&&seleccion.activa&&<button type="button" className="mp-boton peligro" onClick={()=>setConfirmar(true)}>Desactivar prestación</button>}{seleccion&&!seleccion.activa&&<button type="button" className="mp-boton secundario" disabled={reactivando} onClick={()=>void reactivar()}>{reactivando?"Reactivando…":"Reactivar prestación"}</button>}<span/><button type="button" className="mp-boton secundario" onClick={()=>setModal(false)}>Cancelar</button><button className="mp-boton primario" disabled={guardando||reactivando}>{guardando?(seleccion?"Guardando…":"Creando…"):(seleccion?"Guardar cambios":"Crear prestación")}</button></footer></form></div>}
    {confirmar&&<div className="mp-overlay confirmar" role="dialog" aria-modal="true"><div className="mp-modal mp-confirmar"><h2>Desactivar prestación</h2><p>La prestación dejará de estar disponible para nuevas reservas. Los turnos ya creados no serán modificados.</p><footer><button className="mp-boton secundario" onClick={()=>setConfirmar(false)}>Cancelar</button><button className="mp-boton peligro-solido" onClick={()=>void desactivar()}>Desactivar</button></footer></div></div>}
  </ProfesionalShell>
}
