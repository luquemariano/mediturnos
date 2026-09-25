from __future__ import annotations

from dataclasses import dataclass
import os

GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
DEFAULT_SITE_URL = "sc-domain:turnelia.com.ar"


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
        return cls(**values)
