import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from streamator import JobLogger
from streamator import fastapi as sf


@pytest.fixture(autouse=True)
def clear_registry():
    sf._loggers.clear()
    yield
    sf._loggers.clear()


# --- JobLogger ---

def test_job_id_is_unique():
    a, b = JobLogger(), JobLogger()
    assert a.job_id != b.job_id


def test_log_entry_shape():
    logger = JobLogger()
    logger.log("hello")
    entries = logger._store.snapshot()
    assert len(entries) == 1
    e = entries[0]
    assert e["event"] == "log"
    assert e["message"] == "hello"
    assert e["level"] == "info"
    assert isinstance(e["t"], float)


def test_log_levels():
    logger = JobLogger()
    for level in ("info", "success", "warning", "error"):
        logger.log("msg", level=level)
    levels = [e["level"] for e in logger._store.snapshot()]
    assert levels == ["info", "success", "warning", "error"]


# --- MemoryStore streaming ---

async def test_memory_store_stream():
    logger = JobLogger()
    logger.log("a")
    logger.log("b")
    logger.close()

    received = []
    async for entry in logger._store.stream():
        received.append(entry["message"])

    assert received == ["a", "b"]


# --- FastAPI routes ---

@pytest.fixture
def app_client():
    app = FastAPI()
    sf.add_log_routes(app)
    return TestClient(app)


def test_snapshot_route(app_client):
    logger = JobLogger()
    logger.log("step 1")
    logger.log("step 2")

    resp = app_client.get(f"/log/{logger.job_id}")
    assert resp.status_code == 200
    logs = resp.json()["logs"]
    assert len(logs) == 2
    assert logs[0]["message"] == "step 1"


def test_snapshot_not_found(app_client):
    resp = app_client.get("/log/nonexistent")
    assert resp.status_code == 404


def test_stream_route(app_client):
    logger = JobLogger()
    logger.log("streamed")
    logger.close()

    with app_client.stream("GET", f"/log/{logger.job_id}/stream") as resp:
        assert resp.status_code == 200
        chunks = list(resp.iter_lines())

    data_lines = [l for l in chunks if l.startswith("data:")]
    assert any("streamed" in l for l in data_lines)


def test_stream_not_found(app_client):
    resp = app_client.get("/log/nonexistent/stream")
    assert resp.status_code == 404
