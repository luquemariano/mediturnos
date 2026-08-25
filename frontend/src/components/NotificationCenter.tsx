import { useEffect, useState } from "react";
import api from "../api/api";
import type { NotificationItem } from "../types/paciente";
import "./NotificationCenter.css";

export default function NotificationCenter({ onOpen }: { onOpen?: (item: NotificationItem) => void }) {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  useEffect(() => { void api.get<{ items: NotificationItem[]; unread_count: number }>("/notifications").then((r) => { setItems(r.data.items); setUnread(r.data.unread_count); }).catch(() => undefined); }, []);
  async function read(item: NotificationItem) { if (!item.read_at) { await api.post(`/notifications/${item.id}/read`); setItems((current) => current.map((x) => x.id === item.id ? { ...x, read_at: new Date().toISOString() } : x)); setUnread((value) => Math.max(0, value - 1)); } onOpen?.(item); }
  const alerta = unread > 0;
  return <div className="notification-center"><button type="button" className={`notification-trigger${alerta ? " notification-trigger-alerta" : ""}`} aria-label={`Notificaciones${unread ? `, ${unread} sin leer` : ""}`} title="Notificaciones" aria-expanded={open} onClick={() => setOpen((value) => !value)}><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></svg>{alerta && <b>{unread > 99 ? "99+" : unread}</b>}</button>{open && <div className="notification-popover" role="dialog" aria-label="Notificaciones"><header><strong>Novedades</strong><button type="button" aria-label="Cerrar notificaciones" onClick={() => setOpen(false)}>×</button></header>{items.length ? <ul>{items.map((item) => <li key={item.id} className={item.read_at ? "leida" : "nueva"}><button type="button" onClick={() => void read(item)}><span>{item.message}</span><time>{new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short" }).format(new Date(item.created_at))}</time></button></li>)}</ul> : <p>No hay notificaciones nuevas.</p>}</div>}</div>;
}
