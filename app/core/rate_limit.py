from collections import defaultdict, deque
from collections.abc import Callable
from ipaddress import ip_address
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request

from app.core.config import settings


class RateLimiter:
    def __init__(self) -> None:
        self._intentos: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def verificar(self, clave: str, limite: int, ventana_segundos: int) -> None:
        ahora = monotonic()
        umbral = ahora - ventana_segundos
        with self._lock:
            intentos = self._intentos[clave]
            while intentos and intentos[0] <= umbral:
                intentos.popleft()
            if len(intentos) >= limite:
                espera = max(1, int(ventana_segundos - (ahora - intentos[0])))
                raise HTTPException(
                    status_code=429,
                    detail="Demasiados intentos. Esperá un momento antes de volver a intentar.",
                    headers={"Retry-After": str(espera)},
                )
            intentos.append(ahora)

    def reiniciar(self) -> None:
        with self._lock:
            self._intentos.clear()


rate_limiter = RateLimiter()


def obtener_ip_cliente(request: Request) -> str:
    directa = request.client.host if request.client is not None else "desconocida"
    if not settings.trust_proxy_headers:
        return directa

    encabezado = request.headers.get("x-forwarded-for", "")
    candidata = encabezado.split(",", maxsplit=1)[0].strip()
    try:
        return str(ip_address(candidata))
    except ValueError:
        return directa


def limitar(nombre: str, limite: int, ventana_segundos: int) -> Callable:
    def dependencia(request: Request) -> None:
        ip = obtener_ip_cliente(request)
        rate_limiter.verificar(f"{nombre}:{ip}", limite, ventana_segundos)

    return dependencia


limitar_registro = limitar(
    "registro",
    settings.rate_limit_register_attempts,
    settings.rate_limit_window_seconds,
)
limitar_login = limitar(
    "login",
    settings.rate_limit_login_attempts,
    settings.rate_limit_window_seconds,
)
limitar_recuperacion = limitar(
    "recuperacion",
    settings.rate_limit_password_reset_attempts,
    settings.rate_limit_window_seconds,
)

limitar_reset_admin = limitar(
    "reset_admin_interno",
    3,
    60,
)
