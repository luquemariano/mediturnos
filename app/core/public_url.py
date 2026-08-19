from ipaddress import ip_address
from urllib.parse import urlsplit, urlunsplit


def validar_public_api_url(valor: str, *, production: bool) -> str:
    partes = urlsplit(valor.strip())
    if partes.scheme not in {"http", "https"} or not partes.hostname:
        raise ValueError("PUBLIC_API_URL debe ser una URL HTTP o HTTPS válida.")
    if partes.username or partes.password or partes.query or partes.fragment:
        raise ValueError("PUBLIC_API_URL no puede contener credenciales, query ni fragment.")
    host = partes.hostname.rstrip(".").lower()
    try:
        loopback = ip_address(host).is_loopback
    except ValueError:
        loopback = host == "localhost"
    if production and (loopback or partes.scheme != "https"):
        raise ValueError("En production, PUBLIC_API_URL debe usar HTTPS y no loopback.")
    return urlunsplit((partes.scheme, partes.netloc, partes.path.rstrip("/"), "", ""))
