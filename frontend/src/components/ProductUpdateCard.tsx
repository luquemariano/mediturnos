import { ACTIVE_PRODUCT_UPDATE } from "../productUpdates";
import "./ProductUpdateCard.css";

type Props = { onOpen: (path: string) => void };

export default function ProductUpdateCard({ onOpen }: Props) {
  const update = ACTIVE_PRODUCT_UPDATE;
  if (!update) return null;
  return <aside className="product-update" aria-labelledby="product-update-title">
    <div className="product-update__mark" aria-hidden="true">✦</div>
    <div className="product-update__body"><span className="product-update__badge">{update.badge}</span><h2 id="product-update-title">{update.title}</h2><p>{update.description}</p><div className="product-update__actions"><button type="button" onClick={() => onOpen(update.ctaPath)}>{update.ctaLabel}</button><button type="button" className="product-update__help" onClick={() => onOpen(update.helpPath)}>Cómo funciona</button></div></div>
  </aside>;
}
