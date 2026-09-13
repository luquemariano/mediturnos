import { useState } from "react";
import { ACTIVE_PRODUCT_UPDATE, productUpdateStorageKey } from "../productUpdates";
import "./ProductUpdateCard.css";

type Props = { userKey: string; onOpen: (path: string) => void };

export default function ProductUpdateCard({ userKey, onOpen }: Props) {
  const update = ACTIVE_PRODUCT_UPDATE;
  const key = update ? productUpdateStorageKey(update.id, userKey) : "turnelia:product-update:none";
  const [dismissed, setDismissed] = useState(() => update ? localStorage.getItem(key) === "dismissed" : true);
  if (!update) return null;
  if (dismissed) return null;
  const dismiss = () => { localStorage.setItem(key, "dismissed"); setDismissed(true); };
  return <aside className="product-update" aria-labelledby="product-update-title">
    <div className="product-update__mark" aria-hidden="true">✦</div>
    <div className="product-update__body"><span className="product-update__badge">{update.badge}</span><h2 id="product-update-title">{update.title}</h2><p>{update.description}</p><div className="product-update__actions"><button type="button" onClick={() => { dismiss(); onOpen(update.ctaPath); }}>{update.ctaLabel}</button><button type="button" className="product-update__help" onClick={() => { dismiss(); onOpen(update.helpPath); }}>Cómo funciona</button><button type="button" className="product-update__close" aria-label="Cerrar novedad" onClick={dismiss}>×</button></div></div>
  </aside>;
}
