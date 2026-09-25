from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
from threading import Event
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser

import requests

from app.core.gsc_config import DEFAULT_SITE_URL, GSC_SCOPE

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def load_desktop_credentials(path: Path) -> tuple[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    installed = data.get("installed")
    if not isinstance(installed, dict):
        raise ValueError("Se requieren credenciales OAuth tipo Desktop app.")
    client_id = str(installed.get("client_id", "")).strip()
    client_secret = str(installed.get("client_secret", "")).strip()
    if not client_id or not client_secret:
        raise ValueError("El JSON OAuth no contiene client_id/client_secret.")
    return client_id, client_secret


def build_auth_url(client_id: str, redirect_uri: str) -> str:
    return AUTH_URL + "?" + urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GSC_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "false",
    })


class CallbackHandler(BaseHTTPRequestHandler):
    code: str | None = None
    error: str | None = None
    done = Event()

    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        type(self).code = (query.get("code") or [None])[0]
        type(self).error = (query.get("error") or [None])[0]
        body = (
            "Autorización recibida. Podés cerrar esta ventana."
            if type(self).code
            else "No se pudo completar la autorización."
        )
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        type(self).done.set()

    def log_message(self, fmt: str, *args: object) -> None:
        return


def exchange_code(
    *,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    session=requests,
) -> str:
    response = session.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(
            f"Google OAuth devolvió HTTP {response.status_code}."
        )
    refresh_token = response.json().get("refresh_token")
    if not refresh_token:
        raise RuntimeError(
            "Google no devolvió refresh_token. Revocá el consentimiento "
            "previo y repetí el flujo con prompt=consent."
        )
    return str(refresh_token)


def mask(value: str) -> str:
    if len(value) <= 10:
        return "***"
    return value[:6] + "…" + value[-4:]


def write_env(
    path: Path,
    *,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    site_url: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        f"GSC_CLIENT_ID={client_id}\n"
        f"GSC_CLIENT_SECRET={client_secret}\n"
        f"GSC_REFRESH_TOKEN={refresh_token}\n"
        f"GSC_SITE_URL={site_url}\n"
    )
    path.write_text(payload, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--credentials", required=True)
    parser.add_argument("--env-output")
    parser.add_argument("--site-url", default=DEFAULT_SITE_URL)
    args = parser.parse_args()

    client_id, client_secret = load_desktop_credentials(
        Path(args.credentials)
    )
    CallbackHandler.code = None
    CallbackHandler.error = None
    CallbackHandler.done.clear()
    server = HTTPServer(("127.0.0.1", 0), CallbackHandler)
    redirect_uri = f"http://127.0.0.1:{server.server_port}/"
    auth_url = build_auth_url(client_id, redirect_uri)

    print(f"OAuth client: {mask(client_id)}")
    print("Scope: webmasters.readonly")
    print("Abriendo Google en tu navegador local…")
    webbrowser.open(auth_url)

    while not CallbackHandler.done.is_set():
        server.handle_request()
    server.server_close()

    if CallbackHandler.error:
        raise RuntimeError(
            f"Google devolvió un error OAuth: {CallbackHandler.error}"
        )
    if not CallbackHandler.code:
        raise RuntimeError("No se recibió código OAuth.")

    refresh_token = exchange_code(
        client_id=client_id,
        client_secret=client_secret,
        code=CallbackHandler.code,
        redirect_uri=redirect_uri,
    )
    print("Refresh token obtenido: sí")
    print(
        "Variables: GSC_CLIENT_ID, GSC_CLIENT_SECRET, "
        "GSC_REFRESH_TOKEN, GSC_SITE_URL"
    )
    if args.env_output:
        output = Path(args.env_output)
        write_env(
            output,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            site_url=args.site_url,
        )
        print(f"Archivo de entorno creado: {output}")
    else:
        print(
            "No se escribió ningún secreto. Usá --env-output PATH "
            "para guardarlos localmente."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
