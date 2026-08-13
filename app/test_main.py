import os
import tempfile
import pytest

os.environ["DB_PATH"] = tempfile.mktemp(suffix=".db")

from main import app, init_db  # noqa: E402


@pytest.fixture
def client():
    init_db()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_version(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    assert "version" in resp.get_json()


def test_create_task_requires_title(client):
    resp = client.post("/tasks", json={})
    assert resp.status_code == 400


def test_create_and_list_task(client):
    resp = client.post("/tasks", json={"title": "Write pipeline"})
    assert resp.status_code == 201
    task_id = resp.get_json()["id"]

    resp = client.get("/tasks")
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.get_json()]
    assert "Write pipeline" in titles

    resp = client.post(f"/tasks/{task_id}/complete")
    assert resp.status_code == 200
    assert resp.get_json()["done"] is True
