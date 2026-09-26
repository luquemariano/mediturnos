from __future__ import annotations

from dataclasses import dataclass
import os
import re

GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
DEFAULT_SITE_URL = "sc-domain:turnelia.com.ar"
_DOMAIN_PROPERTY_RE = re.compile(r"^sc-domain:[A-Za-z0-9.-]+$")


def validate_site_url(site_url: str) -> str:
    """Validate a Search Console domain or URL-prefix property."""
    if not site_url or any(char.isspace() for char in site_url):
        raise ValueError("GSC_SITE_URL debe ser una propiedad válida de Search Console.")
    if _DOMAIN_PROPERTY_RE.fullmatch(site_url):
        return site_url
    if site_url.startswith(("http://", "https://")):
        from urllib.parse import urlsplit

        parsed = urlsplit(site_url)
        if parsed.netloc and not parsed.username and not parsed.password:
            return site_url
    raise ValueError("GSC_SITE_URL debe ser sc-domain:dominio o una URL http(s).")


@dataclass(frozen=True)
class GSCConfig:
    client_id: str
    client_secret: str
    refresh_token: str
    site_url: str = DEFAULT_SITE_URL

    @classmethod
    def from_env(cls) -> "GSCConfig":
        values = {
            "client_id": os.getenv("GSC_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("GSC_CLIENT_SECRET", "").strip(),
            "refresh_token": os.getenv("GSC_REFRESH_TOKEN", "").strip(),
            "site_url": os.getenv("GSC_SITE_URL", DEFAULT_SITE_URL).strip(),
        }
        missing = [
            name for name in ("client_id", "client_secret", "refresh_token")
            if not values[name]
        ]
        if missing:
            raise RuntimeError(
                "Faltan variables GSC requeridas: " + ", ".join(missing)
            )
        values["site_url"] = validate_site_url(values["site_url"])
        return cls(**values)
