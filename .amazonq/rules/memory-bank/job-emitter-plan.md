# JobEmitter — Implementation Battle Plan

## Decisions

- `JobEmitter` wraps `JobLogger` — no parallel implementation
- Class methods (`cancel`, `pop_result`, `exists`) are in-process only; no-op/return None for unknown job IDs
- Background reaper is off by default; opt-in via `start_reaper()`
- `emit()` / `log()` after `close()` log a `warnings.warn()` and no-op
- `add_log_routes` logs a deprecation warning via `warnings.warn()` but still works
- DynamoDB support deferred to a later step

---

## Steps

### Step 1 — `JobEmitter` core class (`emitter.py`)
- [x] New file `python/streamator/emitter.py`
- [x] `JobEmitter.__init__(store, **kwargs)` — instantiates a `JobLogger` internally
- [x] `emit(event: dict)` — adds `t`, appends to store; warns + no-ops if closed
- [x] `log(message, level)` — delegates to inner `JobLogger.log()`; warns + no-ops if closed
- [x] `track(task)` — stores `asyncio.Task` reference in module-level `_emitters` dict
- [x] `set_result(data)` — stores result in module-level `_results` dict
- [x] `close()` — idempotent; sets closed flag, delegates to `JobLogger.close()`
- [x] `async __aenter__` / `__aexit__` — calls `close()` on exit (even on exception)
- [x] `job_id` property — delegates to inner logger
- [x] `JobEmitter.cancel(job_id)` — cancels tracked task if present; silent no-op otherwise
- [x] `JobEmitter.pop_result(job_id)` — pops and returns result or `None`
- [x] `JobEmitter.exists(job_id)` — checks `_emitters` registry

### Step 2 — Wire into `__init__.py` and registry
- [x] Export `JobEmitter` from `streamator/__init__.py`
- [x] `JobEmitter.__init__` registers self in module-level `_emitters` dict (same pattern as `_loggers` in fastapi.py)

### Step 3 — FastAPI helpers (`fastapi.py`)
- [x] Add `_emitters` import / reference from `emitter.py`
- [x] `make_job_stream_response(job_id)` — looks up `_emitters`, returns SSE or 404
- [x] `add_job_routes(app_or_router, prefix)` — mounts stream + result + cancel routes
- [x] `add_log_routes` — add `warnings.warn(..., DeprecationWarning)` at call site

### Step 4 — Background reaper
- [x] `start_reaper(ttl_seconds, interval)` async function in `emitter.py`
- [x] Loops, evicts expired entries from `_emitters` and `_results`, cancels tasks
- [x] Must be awaited / `create_task`'d by caller (FastAPI lifespan or manual)

### Step 5 — Tests
- [x] `JobEmitter` basic: unique IDs, `emit()` shape, `log()` shape, `set_result` / `pop_result`
- [x] `emit()` after `close()` triggers warning and no-ops
- [x] `cancel()` cancels task; safe on unknown ID
- [x] `exists()` returns correct bool
- [x] Context manager closes on normal exit and on exception
- [x] FastAPI: stream route, result route, cancel route, 404 cases
- [x] Deprecation warning on `add_log_routes`

### Step 6 — Documentation
- [ ] Update / create `python/.ai-docs/streamator.md` with `JobEmitter` API reference
- [ ] Update `specs.md` with `JobEmitter` section and migration guide
- [ ] Update `structure.md` memory-bank doc to include `emitter.py`

---

## File Changelist

| File | Change |
|------|--------|
| `python/streamator/emitter.py` | New |
| `python/streamator/__init__.py` | Add `JobEmitter` export |
| `python/streamator/fastapi.py` | Add job routes; deprecate `add_log_routes` |
| `python/tests/test_backend.py` | Add `JobEmitter` + new route tests |
| `python/.ai-docs/streamator.md` | New or update |
| `specs.md` | Update |
| `.amazonq/rules/memory-bank/structure.md` | Update `emitter.py` entry |
