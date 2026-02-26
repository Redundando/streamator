# streamator

Backend logging primitive for long-running async jobs. Stream timestamped log messages
to a browser UI via SSE or polling — no WebSockets, no custom infrastructure.

Pairs with [`streamator-react`](https://www.npmjs.com/package/streamator-react) on the frontend.

## Install

```bash
pip install streamator                    # core only (in-memory)
pip install streamator[fastapi]           # + FastAPI route helpers
pip install streamator[dynamo]            # + DynamoDB backend
pip install streamator[fastapi,dynamo]    # everything
```

## Usage

```python
from streamator import JobLogger

async def my_job(logger: JobLogger):
    logger.log("Starting…")
    await do_work()
    logger.log("Done", level="success")
    logger.close()

@router.post("/start")
async def start():
    logger = JobLogger()
    asyncio.create_task(my_job(logger))
    return {"log_job_id": logger.job_id}
```

Or use the context manager — `close()` is called automatically, even on exception:

```python
async with JobLogger() as logger:
    logger.log("Starting…")
    await do_work()
    logger.log("Done", level="success")
```

## FastAPI integration

```python
from streamator.fastapi import add_log_routes

add_log_routes(app, prefix="/log")
# GET /log/{job_id}/stream  → SSE stream
# GET /log/{job_id}         → { logs: [...] } snapshot
```

## Storage backends

**Memory** (default) — `asyncio.Queue`, SSE push, zero dependencies, single-process only.

**DynamoDB** — persists across restarts, readable by polling, distributed-friendly.

```python
logger = JobLogger(store="dynamo", table="my-logs-table", ttl_days=1)
```

## Log levels

`"info"` (default) · `"success"` · `"warning"` · `"error"`

## Log entry format

```python
{"event": "log", "message": "...", "level": "info", "t": 1.23}
```

`t` is seconds since the logger was created, computed at the moment `log()` is called.
