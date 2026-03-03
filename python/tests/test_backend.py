import asyncio
import warnings
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from streamator import JobLogger, JobEmitter
from streamator import fastapi as sf
from streamator import emitter as se


@pytest.fixture(autouse=True)
def clear_registry():
    sf._loggers.clear()
    se._emitters.clear()
    se._results.clear()
    yield
    sf._loggers.clear()
    se._emitters.clear()
    se._results.clear()


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


def test_add_log_routes_deprecation_warning():
    app = FastAPI()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        sf.add_log_routes(app)
    assert any(issubclass(x.category, DeprecationWarning) for x in w)


# --- JobEmitter ---

def test_emitter_job_id_is_unique():
    a, b = JobEmitter(), JobEmitter()
    assert a.job_id != b.job_id


def test_emitter_emit_shape():
    emitter = JobEmitter()
    emitter.emit({"event": "progress", "step": 1})
    entries = emitter._logger._store.snapshot()
    assert len(entries) == 1
    e = entries[0]
    assert e["event"] == "progress"
    assert e["step"] == 1
    assert isinstance(e["t"], float)


def test_emitter_log_shape():
    emitter = JobEmitter()
    emitter.log("hello", level="success")
    entries = emitter._logger._store.snapshot()
    assert len(entries) == 1
    e = entries[0]
    assert e["event"] == "log"
    assert e["message"] == "hello"
    assert e["level"] == "success"


def test_emitter_set_and_pop_result():
    emitter = JobEmitter()
    emitter.set_result({"total": 42})
    result = JobEmitter.pop_result(emitter.job_id)
    assert result == {"total": 42}
    assert JobEmitter.pop_result(emitter.job_id) is None


def test_emitter_exists():
    emitter = JobEmitter()
    assert JobEmitter.exists(emitter.job_id)
    assert not JobEmitter.exists("nonexistent")


def test_emitter_emit_after_close_warns():
    emitter = JobEmitter()
    emitter.close()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        emitter.emit({"event": "late"})
    assert len(w) == 1
    assert "emit()" in str(w[0].message)
    assert emitter._logger._store.snapshot() == []


def test_emitter_log_after_close_warns():
    emitter = JobEmitter()
    emitter.close()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        emitter.log("late")
    assert len(w) == 1
    assert "log()" in str(w[0].message)


def test_emitter_close_is_idempotent():
    emitter = JobEmitter()
    emitter.close()
    emitter.close()  # should not raise


def test_emitter_cancel_unknown_id():
    JobEmitter.cancel("nonexistent")  # should not raise


async def test_emitter_cancel_task():
    emitter = JobEmitter()
    task = asyncio.create_task(asyncio.sleep(60))
    emitter.track(task)
    JobEmitter.cancel(emitter.job_id)
    await asyncio.sleep(0)
    assert task.cancelled()


async def test_emitter_context_manager_closes():
    async with JobEmitter() as emitter:
        emitter.emit({"event": "started"})
    assert emitter._closed


async def test_emitter_context_manager_closes_on_exception():
    with pytest.raises(RuntimeError):
        async with JobEmitter() as emitter:
            raise RuntimeError("boom")
    assert emitter._closed


# --- JobEmitter FastAPI routes ---

@pytest.fixture
def job_app_client():
    app = FastAPI()
    sf.add_job_routes(app)
    return TestClient(app)


def test_job_stream_route(job_app_client):
    emitter = JobEmitter()
    emitter.emit({"event": "progress", "step": 1})
    emitter.close()

    with job_app_client.stream("GET", f"/job/{emitter.job_id}/stream") as resp:
        assert resp.status_code == 200
        chunks = list(resp.iter_lines())

    data_lines = [l for l in chunks if l.startswith("data:")]
    assert any("progress" in l for l in data_lines)
    assert any("done" in l for l in data_lines)


def test_job_stream_not_found(job_app_client):
    resp = job_app_client.get("/job/nonexistent/stream")
    assert resp.status_code == 404


def test_job_result_route(job_app_client):
    emitter = JobEmitter()
    emitter.set_result({"count": 7})

    resp = job_app_client.get(f"/job/{emitter.job_id}/result")
    assert resp.status_code == 200
    assert resp.json() == {"count": 7}


def test_job_result_not_found(job_app_client):
    emitter = JobEmitter()
    resp = job_app_client.get(f"/job/{emitter.job_id}/result")
    assert resp.status_code == 404


def test_job_cancel_route(job_app_client):
    emitter = JobEmitter()
    resp = job_app_client.post(f"/job/{emitter.job_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["cancelled"] == emitter.job_id
