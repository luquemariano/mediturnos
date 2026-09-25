from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
from typing import Any
from urllib.parse import quote

import requests

from app.core.gsc_config import GSCConfig

SEARCH_ANALYTICS_URL = (
    "https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
)
TOKEN_URL = "https://oauth2.googleapis.com/token"
ROW_LIMIT = 25000


class GSCError(RuntimeError):
    pass


@dataclass(frozen=True)
class DateRanges:
    start: date
    end: date
    comparison_start: date
    comparison_end: date


def calculate_ranges(
    *,
    days: int = 28,
    lag_days: int = 3,
    start_date: date | None = None,
    end_date: date | None = None,
    today: date | None = None,
) -> DateRanges:
    if days <= 0 or lag_days < 0:
        raise ValueError("days debe ser > 0 y lag_days >= 0")
    if (start_date is None) != (end_date is None):
        raise ValueError("start_date y end_date deben indicarse juntos")
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise ValueError("start_date no puede ser posterior a end_date")
        start, end = start_date, end_date
        span = (end - start).days + 1
    else:
        ref = today or date.today()
        end = ref - timedelta(days=lag_days)
        start = end - timedelta(days=days - 1)
        span = days
    comparison_end = start - timedelta(days=1)
    comparison_start = comparison_end - timedelta(days=span - 1)
    return DateRanges(start, end, comparison_start, comparison_end)


def _safe_error(response: requests.Response) -> GSCError:
    return GSCError(
        f"Google Search Console API devolvió HTTP {response.status_code}."
    )


def refresh_access_token(config: GSCConfig, session=requests) -> str:
    response = session.post(
        TOKEN_URL,
        data={
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "refresh_token": config.refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if not response.ok:
        raise _safe_error(response)
    token = response.json().get("access_token")
    if not token:
        raise GSCError("Google no devolvió access_token.")
    return str(token)


class GSCClient:
    def __init__(
        self,
        config: GSCConfig,
        *,
        session=requests,
        max_pages: int = 20,
    ) -> None:
        self.config = config
        self.session = session
        self.max_pages = max_pages
        self._access_token: str | None = None

    def _token(self) -> str:
        if self._access_token is None:
            self._access_token = refresh_access_token(
                self.config, self.session
            )
        return self._access_token

    def query(
        self,
        start: date,
        end: date,
        dimensions: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        site = quote(self.config.site_url, safe="")
        url = SEARCH_ANALYTICS_URL.format(site=site)
        start_row = 0
        for _ in range(self.max_pages):
            body: dict[str, Any] = {
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
                "type": "web",
                "rowLimit": ROW_LIMIT,
                "startRow": start_row,
            }
            if dimensions:
                body["dimensions"] = dimensions
            response = self.session.post(
                url,
                headers={
                    "Authorization": f"Bearer {self._token()}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=60,
            )
            if not response.ok:
                raise _safe_error(response)
            batch = response.json().get("rows") or []
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < ROW_LIMIT:
                break
            start_row += len(batch)
        else:
            raise GSCError(
                "Se alcanzó el límite defensivo de paginación."
            )
        return rows


def _metric_row(row: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    values = row.get("keys") or []
    parsed = {name: values[i] for i, name in enumerate(keys)}
    parsed.update(
        clicks=float(row.get("clicks", 0)),
        impressions=float(row.get("impressions", 0)),
        ctr=float(row.get("ctr", 0)),
        position=float(row.get("position", 0)),
    )
    return parsed


def parse_rows(
    rows: list[dict[str, Any]],
    dimensions: list[str],
) -> list[dict[str, Any]]:
    return [_metric_row(row, dimensions) for row in rows]


def summary_from_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {
            "clicks": 0.0,
            "impressions": 0.0,
            "ctr": 0.0,
            "average_position": 0.0,
        }
    row = rows[0]
    return {
        "clicks": float(row.get("clicks", 0)),
        "impressions": float(row.get("impressions", 0)),
        "ctr": float(row.get("ctr", 0)),
        "average_position": float(row.get("position", 0)),
    }


def build_opportunities(
    query_pages: list[dict[str, Any]],
    *,
    min_impressions: float = 10,
    min_position: float = 4,
    max_position: float = 20,
) -> list[dict[str, Any]]:
    result = [
        row for row in query_pages
        if row["impressions"] >= min_impressions
        and min_position <= row["position"] <= max_position
    ]
    return sorted(
        result,
        key=lambda row: (-row["impressions"], row["position"]),
    )


def build_new_queries(
    current: list[dict[str, Any]],
    previous: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    previous_names = {row["query"] for row in previous}
    return [
        row for row in current
        if row["impressions"] > 0 and row["query"] not in previous_names
    ]


def collect_snapshot(
    client: GSCClient,
    ranges: DateRanges,
) -> dict[str, Any]:
    start, end = ranges.start, ranges.end
    summary = summary_from_rows(client.query(start, end))
    daily = parse_rows(client.query(start, end, ["date"]), ["date"])
    queries = parse_rows(client.query(start, end, ["query"]), ["query"])
    pages = parse_rows(client.query(start, end, ["page"]), ["page"])
    query_pages = parse_rows(
        client.query(start, end, ["query", "page"]),
        ["query", "page"],
    )
    countries = parse_rows(
        client.query(start, end, ["country"]), ["country"]
    )
    devices = parse_rows(
        client.query(start, end, ["device"]), ["device"]
    )
    previous_queries = parse_rows(
        client.query(
            ranges.comparison_start,
            ranges.comparison_end,
            ["query"],
        ),
        ["query"],
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site_url": client.config.site_url,
        "range": {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "comparison_start_date": ranges.comparison_start.isoformat(),
            "comparison_end_date": ranges.comparison_end.isoformat(),
        },
        "summary": summary,
        "daily": daily,
        "queries": queries,
        "pages": pages,
        "query_pages": query_pages,
        "countries": countries,
        "devices": devices,
        "opportunities": build_opportunities(query_pages),
        "new_queries": build_new_queries(queries, previous_queries),
    }


def write_snapshot(
    snapshot: dict[str, Any],
    root: Path,
    *,
    force: bool = False,
) -> tuple[Path, Path]:
    history = root / "history"
    history.mkdir(parents=True, exist_ok=True)
    root.mkdir(parents=True, exist_ok=True)
    day = snapshot["generated_at"][:10]
    history_path = history / f"{day}.json"
    if history_path.exists() and not force:
        raise FileExistsError(
            f"El snapshot histórico ya existe: {history_path}"
        )
    payload = json.dumps(
        snapshot, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=root,
        delete=False,
    ) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)
    tmp_path.replace(root / "latest.json")
    history_path.write_text(payload, encoding="utf-8")
    return root / "latest.json", history_path


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--lag-days", type=int, default=3)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output-root", default="var/seo/gsc")
    args = parser.parse_args()
    ranges = calculate_ranges(
        days=args.days,
        lag_days=args.lag_days,
        start_date=_parse_date(args.start_date),
        end_date=_parse_date(args.end_date),
    )
    config = GSCConfig.from_env()
    client = GSCClient(config)
    print(
        f"GSC: consultando {ranges.start}..{ranges.end} "
        f"para {config.site_url}"
    )
    snapshot = collect_snapshot(client, ranges)
    for name in (
        "daily", "queries", "pages", "query_pages",
        "countries", "devices", "opportunities", "new_queries",
    ):
        print(f"{name}: {len(snapshot[name])} filas")
    if args.dry_run:
        print(json.dumps(snapshot["summary"], ensure_ascii=False))
        return 0
    latest, history = write_snapshot(
        snapshot, Path(args.output_root), force=args.force
    )
    print(f"latest: {latest}")
    print(f"history: {history}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
