import { useEffect, useRef, useState } from "react";

type Props = { src: string; alt: string };

export default function HelpImage({ src, alt }: Props) {
  const [open, setOpen] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const close = useRef<HTMLButtonElement>(null);
  const wasOpen = useRef(false);
  useEffect(() => {
    if (open) {
      wasOpen.current = true;
      close.current?.focus();
      const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
      document.addEventListener("keydown", onKeyDown);
      return () => document.removeEventListener("keydown", onKeyDown);
    }
    if (wasOpen.current) {
      trigger.current?.focus();
      wasOpen.current = false;
    }
  }, [open]);
  return <>
    <button ref={trigger} type="button" aria-label={`Ampliar imagen: ${alt}`} style={{ display: "block", maxWidth: "100%", padding: 0, border: 0, background: "none", cursor: "zoom-in" }} onClick={() => setOpen(true)}><img src={src} alt={alt} /></button>
    {open && <div role="presentation" onClick={() => setOpen(false)} style={{ position: "fixed", inset: 0, zIndex: 20, display: "grid", placeItems: "center", padding: "4vh 2vw", background: "rgba(13,30,28,.82)" }}><section role="dialog" aria-modal="true" aria-label={alt} onClick={(event) => event.stopPropagation()} style={{ position: "relative", maxWidth: "min(96vw, 1440px)", maxHeight: "92vh" }}><button ref={close} type="button" aria-label="Cerrar" onClick={() => setOpen(false)} style={{ position: "absolute", top: -18, right: -18, zIndex: 1, width: 40, height: 40, borderRadius: "50%", background: "#153e3b", color: "white", fontSize: "1.7rem", cursor: "pointer" }}>×</button><img src={src} alt={alt} style={{ maxWidth: "96vw", maxHeight: "92vh", objectFit: "contain", cursor: "zoom-out" }} /></section></div>}
  </>;
}
