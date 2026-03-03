# streamator

Backend primitive for streaming structured events and logs from long-running async jobs
to a browser UI via SSE — no WebSockets, no custom infrastructure.

Pairs with [`streamator-react`](https://www.npmjs.com/package/streamator-react) on the frontend.

## Install

```bash
pip install streamator                    # core only (in-memory)
pip install streamator[fastapi]           # + FastAPI route helpers
pip install streamator[dynamo]            # + DynamoDB backend
pip install streamator[fastapi,dynamo]    # everything
```

## JobEmitter

`JobEmitter` is the recommended API. It supports structured events, task tracking,
cancellation, and result storage — all in one class.

```python
from streamator import JobEmitter
from streamator.fastapi import add_job_routes

add_job_routes(app, prefix="/job")
# GET  /job/{job_id}/stream  → SSE event stream
# GET  /job/{job_id}/result  → stored result (JSON)
# POST /job/{job_id}/cancel  → cancel tracked task

@router.post("/start")
async def start():
    emitter = JobEmitter()

    async def run():
        async with emitter:
            for i in range(1, 6):
                emitter.emit({"event": "progress", "current": i, "total": 5})
                emitter.log(f"Step {i} of 5")
                await do_work()
            emitter.set_result({"steps_completed": 5})
            emitter.log("Done", level="success")

    task = asyncio.create_task(run())
    emitter.track(task)
    return {"job_id": emitter.job_id}
```

### Instance methods

```python
emitter.emit({"event": "progress", "step": 1})  # structured event, t added automatically
emitter.log("Working...", level="info")          # log message shorthand
emitter.track(task)                              # store asyncio.Task for cancellation
emitter.set_result({"count": 42})               # store final result for later retrieval
emitter.close()                                  # idempotent; sends done sentinel
```

Calling `emit()` or `log()` after `close()` logs a warning and no-ops.

### Class methods

```python
JobEmitter.cancel(job_id)       # cancel tracked task; no-op if unknown
JobEmitter.pop_result(job_id)   # fetch and consume result; None if not ready
JobEmitter.exists(job_id)       # check if job is in registry
```

### Event format on the wire

```python
# emit() — passes through with t added
{"event": "progress", "step": 1, "t": 1.23}

# log() — standard log shape
{"event": "log", "message": "Working...", "level": "info", "t": 1.23}

# close() — terminal sentinel
{"event": "done", "t": 5.67}
```

### Background reaper (optional)

```python
from streamator.emitter import start_reaper

# In FastAPI lifespan:
asyncio.create_task(start_reaper(ttl_seconds=300, interval=60))
```

Only evicts closed jobs older than `ttl_seconds`. Off by default.

---

## JobLogger

`JobLogger` is the simpler API for log-only use cases.

```python
from streamator import JobLogger
from streamator.fastapi import add_log_routes

add_log_routes(app, prefix="/log")   # deprecated — use add_job_routes instead

@router.post("/start")
async def start():
    logger = JobLogger()
    asyncio.create_task(my_job(logger))
    return {"log_job_id": logger.job_id}
```

`add_log_routes` still works but emits a `DeprecationWarning`. Migrate to
`add_job_routes` + `JobEmitter` when convenient.

---

## Storage backends

**Memory** (default) — `asyncio.Queue`, SSE push, zero dependencies, single-process only.

**DynamoDB** — persists across restarts, readable by polling, distributed-friendly.

```python
emitter = JobEmitter(store="dynamo", table="my-jobs", ttl_days=1)
```

## Log levels

`"info"` (default) · `"success"` · `"warning"` · `"error"`
