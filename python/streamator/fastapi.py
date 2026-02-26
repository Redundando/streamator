import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse

from .logger import JobLogger

_loggers: dict[str, JobLogger] = {}


def _get(job_id: str) -> JobLogger | None:
    return _loggers.get(job_id)


async def _sse_generator(logger: JobLogger):
    async for entry in logger._store.stream():
        yield f"data: {json.dumps(entry)}\n\n"
    yield f"data: {json.dumps({'event': 'done'})}\n\n"
    _loggers.pop(logger.job_id, None)


def make_stream_response(job_id: str) -> StreamingResponse:
    logger = _get(job_id)
    if logger is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return StreamingResponse(
        _sse_generator(logger),
        media_type="text/event-stream",
    )


def add_log_routes(app: FastAPI, prefix: str = "/log"):
    @app.get(f"{prefix}/{{job_id}}/stream")
    async def stream(job_id: str):
        return make_stream_response(job_id)

    @app.get(f"{prefix}/{{job_id}}")
    async def snapshot(job_id: str):
        logger = _get(job_id)
        if logger is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        logs = logger._store.snapshot()
        if logger._store._closed:
            logs = logs + [{"event": "done"}]
        return {"logs": logs}
