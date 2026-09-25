from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import pytest

from app.core.gsc_config import GSCConfig, GSC_SCOPE
from app.scripts import collect_gsc_snapshot as gsc
from app.scripts import gsc_oauth_bootstrap as oauth


class FakeResponse:
    def __init__(self, payload, *, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def config():
    return GSCConfig("cid", "secret", "refresh", "sc-domain:turnelia.com.ar")


def row(keys=None, clicks=1, impressions=10, ctr=.1, position=5):
    result = {
        "clicks": clicks,
        "impressions": impressions,
        "ctr": ctr,
        "position": position,
    }
    if keys is not None:
        result["keys"] = keys
    return result


def test_default_range_uses_28_days_and_lag_3():
    r = gsc.calculate_ranges(today=date(2026, 9, 25))
    assert r.start == date(2026, 8, 26)
    assert r.end == date(2026, 9, 22)


def test_comparison_range_is_immediately_previous():
    r = gsc.calculate_ranges(today=date(2026, 9, 25))
    assert r.comparison_start == date(2026, 7, 29)
    assert r.comparison_end == date(2026, 8, 25)


def test_explicit_dates_are_respected():
    r = gsc.calculate_ranges(
        start_date=date(2026, 9, 1), end_date=date(2026, 9, 10)
    )
    assert (r.start, r.end) == (date(2026, 9, 1), date(2026, 9, 10))
    assert r.comparison_start == date(2026, 8, 22)


def test_partial_explicit_dates_fail():
    with pytest.raises(ValueError):
        gsc.calculate_ranges(start_date=date(2026, 9, 1))


def test_invalid_days_fail():
    with pytest.raises(ValueError):
        gsc.calculate_ranges(days=0)


def test_refresh_token_returns_access_token():
    session = FakeSession([FakeResponse({"access_token": "abc"})])
    assert gsc.refresh_access_token(config(), session) == "abc"


def test_refresh_error_does_not_expose_body_or_secret():
    session = FakeSession([
        FakeResponse(
            {"error": "secret refresh"}, ok=False, status_code=400
        )
    ])
    with pytest.raises(gsc.GSCError) as exc:
        gsc.refresh_access_token(config(), session)
    message = str(exc.value)
    assert "secret" not in message
    assert "refresh" not in message
    assert "HTTP 400" in message


def test_pagination_uses_start_row(monkeypatch):
    monkeypatch.setattr(gsc, "ROW_LIMIT", 2)
    session = FakeSession([
        FakeResponse({"access_token": "a"}),
        FakeResponse({"rows": [row(["q1"]), row(["q2"])]}),
        FakeResponse({"rows": [row(["q3"])]}),
    ])
    client = gsc.GSCClient(config(), session=session)
    rows = client.query(date(2026, 9, 1), date(2026, 9, 2), ["query"])
    assert len(rows) == 3
    assert session.calls[1][1]["json"]["startRow"] == 0
    assert session.calls[2][1]["json"]["startRow"] == 2


def test_pagination_stops_on_empty(monkeypatch):
    monkeypatch.setattr(gsc, "ROW_LIMIT", 2)
    session = FakeSession([
        FakeResponse({"access_token": "a"}),
        FakeResponse({"rows": []}),
    ])
    client = gsc.GSCClient(config(), session=session)
    assert client.query(date(2026, 9, 1), date(2026, 9, 2)) == []


def test_pagination_defensive_limit(monkeypatch):
    monkeypatch.setattr(gsc, "ROW_LIMIT", 1)
    session = FakeSession([
        FakeResponse({"access_token": "a"}),
        FakeResponse({"rows": [row(["q1"])]}),
    ])
    client = gsc.GSCClient(config(), session=session, max_pages=1)
    with pytest.raises(gsc.GSCError, match="límite defensivo"):
        client.query(date(2026, 9, 1), date(2026, 9, 2), ["query"])


def test_parse_query():
    parsed = gsc.parse_rows([row(["turnos"])], ["query"])
    assert parsed[0]["query"] == "turnos"


def test_parse_page():
    parsed = gsc.parse_rows([row(["https://x/"])], ["page"])
    assert parsed[0]["page"] == "https://x/"


def test_parse_query_page():
    parsed = gsc.parse_rows(
        [row(["turnos", "https://x/"])], ["query", "page"]
    )
    assert parsed[0]["query"] == "turnos"
    assert parsed[0]["page"] == "https://x/"


def test_summary():
    summary = gsc.summary_from_rows(
        [row(clicks=3, impressions=20, ctr=.15, position=4.2)]
    )
    assert summary == {
        "clicks": 3.0,
        "impressions": 20.0,
        "ctr": .15,
        "average_position": 4.2,
    }


def test_opportunities_include_threshold_match():
    rows = [{
        "query": "agenda",
        "page": "https://x/",
        "clicks": 1.0,
        "impressions": 20.0,
        "ctr": .05,
        "position": 6.0,
    }]
    assert gsc.build_opportunities(rows) == rows


@pytest.mark.parametrize(
    "impressions,position",
    [(9, 6), (20, 3.9), (20, 20.1)],
)
def test_opportunities_exclude_outside_thresholds(impressions, position):
    rows = [{
        "query": "x", "page": "p", "clicks": 0.0,
        "impressions": impressions, "ctr": 0.0, "position": position,
    }]
    assert gsc.build_opportunities(rows) == []


def test_new_queries_compare_previous_period():
    current = [
        {"query": "nueva", "impressions": 5},
        {"query": "vieja", "impressions": 7},
    ]
    previous = [{"query": "vieja", "impressions": 3}]
    assert [r["query"] for r in gsc.build_new_queries(current, previous)] == [
        "nueva"
    ]


def snapshot():
    return {
        "generated_at": "2026-09-25T12:00:00+00:00",
        "site_url": "sc-domain:turnelia.com.ar",
        "range": {},
        "summary": {},
        "daily": [], "queries": [], "pages": [], "query_pages": [],
        "countries": [], "devices": [], "opportunities": [],
        "new_queries": [],
    }


def test_write_snapshot_creates_latest_and_history(tmp_path):
    latest, history = gsc.write_snapshot(snapshot(), tmp_path)
    assert latest.exists()
    assert history.exists()
    assert json.loads(latest.read_text())["site_url"].startswith("sc-domain:")


def test_history_is_not_overwritten_without_force(tmp_path):
    gsc.write_snapshot(snapshot(), tmp_path)
    with pytest.raises(FileExistsError):
        gsc.write_snapshot(snapshot(), tmp_path)


def test_force_allows_history_overwrite(tmp_path):
    gsc.write_snapshot(snapshot(), tmp_path)
    gsc.write_snapshot(snapshot(), tmp_path, force=True)


def test_desktop_credentials_required(tmp_path):
    path = tmp_path / "oauth.json"
    path.write_text(json.dumps({"web": {}}))
    with pytest.raises(ValueError, match="Desktop app"):
        oauth.load_desktop_credentials(path)


def test_desktop_credentials_load(tmp_path):
    path = tmp_path / "oauth.json"
    path.write_text(json.dumps({
        "installed": {"client_id": "cid", "client_secret": "sec"}
    }))
    assert oauth.load_desktop_credentials(path) == ("cid", "sec")


def test_auth_url_requests_only_readonly_scope():
    from urllib.parse import parse_qs, urlparse

    url = oauth.build_auth_url("cid", "http://127.0.0.1:1234/")
    params = parse_qs(urlparse(url).query)
    assert params["scope"] == [GSC_SCOPE]
    assert params["access_type"] == ["offline"]
    assert params["prompt"] == ["consent"]


def test_env_output_contains_expected_values(tmp_path):
    path = tmp_path / "gsc.env"
    oauth.write_env(
        path,
        client_id="cid",
        client_secret="sec",
        refresh_token="ref",
        site_url="sc-domain:turnelia.com.ar",
    )
    content = path.read_text()
    assert "GSC_CLIENT_ID=cid" in content
    assert "GSC_CLIENT_SECRET=sec" in content
    assert "GSC_REFRESH_TOKEN=ref" in content
    assert "GSC_SITE_URL=sc-domain:turnelia.com.ar" in content


def test_exchange_error_is_sanitized():
    session = FakeSession([
        FakeResponse(
            {"error_description": "secret-code"},
            ok=False,
            status_code=401,
        )
    ])
    with pytest.raises(RuntimeError) as exc:
        oauth.exchange_code(
            client_id="cid",
            client_secret="supersecret",
            code="code",
            redirect_uri="http://127.0.0.1/",
            session=session,
        )
    assert "supersecret" not in str(exc.value)
    assert "secret-code" not in str(exc.value)


def test_mask_does_not_return_full_client_id():
    value = "1234567890abcdefghij"
    masked = oauth.mask(value)
    assert masked != value
    assert masked.startswith("123456")


def test_snapshot_fixture_contains_no_secrets():
    raw = json.dumps(snapshot())
    for key in ("client_secret", "refresh_token", "access_token"):
        assert key not in raw
