import json
import re
from datetime import datetime

import pytest

from app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_index_structure(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    # Top-level keys
    for key in ("service", "system", "runtime", "request", "endpoints"):
        assert key in data

    # service fields
    svc = data["service"]
    assert svc["name"]
    assert re.match(r"^\d+\.\d+\.\d+", svc["version"])

    # runtime contains uptime_seconds and current_time
    rt = data["runtime"]
    assert isinstance(rt["uptime_seconds"], int)
    # basic ISO time check
    assert isinstance(rt["current_time"], str)
    datetime.fromisoformat(rt["current_time"].replace("Z", "+00:00"))


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("status") == "healthy"
    assert isinstance(data.get("uptime_seconds"), int)


def test_404_returns_json(client):
    resp = client.get("/not-found-path")
    assert resp.status_code == 404
    data = resp.get_json()
    assert "error" in data
