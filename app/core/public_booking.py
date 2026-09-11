import re
import secrets
import unicodedata
import hashlib


PATRON_SLUG_PUBLICO = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LONGITUD_MAXIMA_SLUG_PUBLICO = 120


def es_slug_publico_valido(slug: str) -> bool:
    return (
        isinstance(slug, str)
        and 0 < len(slug) <= LONGITUD_MAXIMA_SLUG_PUBLICO
        and bool(PATRON_SLUG_PUBLICO.fullmatch(slug))
    )


def generar_slug_publico(nombre: str, apellido: str) -> str:
    base = unicodedata.normalize("NFKD", f"{nombre}-{apellido}").encode("ascii", "ignore").decode("ascii").lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "profesional"
    return f"{base[:114].rstrip('-')}-{secrets.token_hex(2)}"


def generar_token_autogestion() -> str:
    return secrets.token_urlsafe(32)


def hash_token_autogestion(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
