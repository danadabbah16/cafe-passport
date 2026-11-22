import pytest

import analytics


def test_rankings_with_stubbed_cafes(client, monkeypatch):
    monkeypatch.setattr(analytics, "load_visits", lambda: [
        {"cafe_id": 1, "visit_date": "2026-11-01", "rating": 9, "price": 3.0},
    ])
    monkeypatch.setattr(analytics, "load_cafe_names", lambda: {1: "HanSo Café"})
    r = client.get("/rankings")
    assert r.status_code == 200
    assert r.get_json()[0]["cafe"] == "HanSo Café"


def test_rankings_when_cafes_down_is_503(client, monkeypatch):
    def down():
        raise analytics.CafesUnavailable("connection refused")
    monkeypatch.setattr(analytics, "load_visits", down)
    r = client.get("/rankings")
    assert r.status_code == 503
    assert r.get_json()["error"] == "cafes service unavailable"


def test_unreachable_cafes_raises_cafes_unavailable(monkeypatch):
    monkeypatch.setattr(analytics, "CAFES_URL", "http://127.0.0.1:9")
    with pytest.raises(analytics.CafesUnavailable):
        analytics.load_visits()


def test_health_is_own_state(client):
    assert client.get("/health").status_code == 200