# Streamator — Package Specification

Two packages in a single monorepo: a Python backend library (`streamator`) and a React
frontend library (`streamator-react`). Both are designed to work together but are
independently usable.

---

## Naming

| | Package name | Registry |
|---|---|---|
| Python | `streamator` | PyPI |
| React | `streamator-react` | npmjs.com |

Follows the existing naming convention: `dynamorator`, `searcherator`, `cacherator`, `logorator`, etc.

---

## Monorepo Structure

```
streamator/
├── python/                   ← PyPI: streamator
│   ├── streamator/
│   │   ├── __init__.py       ← exports JobLogger
│   │   ├── logger.py         ← JobLogger class
│   │   ├── store.py          ← MemoryStore, DynamoStore
│   │   └── fastapi.py        ← FastAPI helpers (optional dep)
│   ├── tests/
│   └── pyproject.toml
└── react/                    ← npm: streamator-react
    ├── src/
    │   ├── index.js          ← exports all public API
    │   ├── useLogStream.js   ← hook
    │   ├── LogPanel.jsx      ← component
    │   ├── formatEvent.js    ← makeFormatEvent + BASE_EVENT_LABELS
    │   └── log.css           ← compiled default styles
    ├── package.json
    └── README.md
```

---

## Python Package — `streamator`

### Purpose
Backend logging primitive for long-running async jobs. Appends timestamped log messages
to a store, which can be streamed to the frontend via SSE or read via polling.

### Storage Backends

**`MemoryStore`** (default)
- Backed by an `asyncio.Queue`
- Messages consumed once — SSE push model
- No persistence, zero extra dependencies
- Best for single-process deployments (FastAPI on one server)

**`DynamoStore`**
- Thin wrapper around `dynamorator.DynamoDBStore`
- Appends to a DynamoDB item's `logs` list
- Persists across restarts, readable by polling
- TTL, compression, and silent failure handling all delegated to `dynamorator`
- Best for distributed deployments or jobs that outlive the web process

### `JobLogger` API

```python
from streamator import JobLogger

# In-memory (default)
logger = JobLogger()
logger = JobLogger(store="memory")

# DynamoDB
logger = JobLogger(store="dynamo", table="my-logs-table", ttl_days=1)

# Logging
logger.log("Scraping https://example.com")
logger.log("Done", level="success")
logger.log("Rate limited", level="warning")
logger.log("Failed to connect", level="error")

# Signal end of stream
logger.close()

# Identity
logger.job_id   # str — unique ID, pass to frontend to connect
logger.start_t  # float — monotonic time at creation, used for t calculation
```

### Log Entry Format

Each entry emitted/stored:
```python
{
    "event": "log",
    "message": "Scraping https://example.com",
    "level": "info",     # "info" | "success" | "warning" | "error"
    "t": 1.23            # seconds since logger was created
}
```

`t` is computed server-side at the moment `log()` is called.

### FastAPI Integration (optional)

```python
from streamator.fastapi import add_log_routes, make_stream_response

# Option A — auto-register routes
add_log_routes(app, prefix="/log")
# Registers:
#   GET /log/{job_id}/stream  → SSE (MemoryStore)
#   GET /log/{job_id}         → { logs: [...] } (DynamoStore or MemoryStore snapshot)

# Option B — manual
@router.get("/log/{job_id}/stream")
def stream(job_id: str):
    return make_stream_response(job_id)
```

### Typical Usage Pattern

```python
async def my_job(logger: JobLogger):
    logger.log("Starting…")
    for item in items:
        await process(item)
        logger.log(f"Processed {item}", level="success")
    logger.close()

@router.post("/start")
async def start():
    logger = JobLogger()
    asyncio.create_task(my_job(logger))
    return {"log_job_id": logger.job_id}
```

### Dependencies & Install Variants

`dynamorator` is used for the DynamoDB backend — it handles table creation, TTL,
compression, and silent failure out of the box.

`logorator` is an optional dev/debug dependency — `JobLogger` internal methods can be
decorated with `@Logger()` during development for visibility into store operations.
Not included in the published package by default.

```bash
pip install streamator                      # core only (MemoryStore)
pip install streamator[fastapi]             # + FastAPI helpers
pip install streamator[dynamo]              # + DynamoDB backend (installs dynamorator)
pip install streamator[fastapi,dynamo]      # everything
```

`pyproject.toml` optional deps:
```toml
[project.optional-dependencies]
dynamo  = ["dynamorator>=0.1.6"]
fastapi = ["fastapi"]
```

---

## React Package — `streamator-react`

### Purpose
Frontend primitives for displaying live log streams from a `streamator` backend (or any
backend emitting the same event format). Handles SSE connection, entry formatting,
auto-scroll, and rendering.

### `useLogStream(url, options)` Hook

```js
import { useLogStream } from 'streamator-react'

// SSE (default)
const { logs, active } = useLogStream('/api/log/abc123/stream')

// With options
const { logs, active } = useLogStream('/api/log/abc123/stream', {
  mode: 'sse',           // 'sse' (default) | 'poll'
  interval: 3000,        // poll interval ms — poll mode only
  formatEvent: fn,       // (rawEvent) => string | null — override message text
                         //   return null to suppress the entry entirely
})
```

**Returns:**
- `logs` — `Array<{ text: string, t: string, level: string }>` — ready to render
- `active` — `boolean` — `true` while stream is open / polling

**Behavior:**
- SSE mode: opens `EventSource`, appends `{ text, t, level }` entries as they arrive.
  `t` is computed client-side as elapsed seconds since connection opened.
- Poll mode: fetches `{ logs: [...] }` on interval, diffs to append only new entries.
  `t` taken from server `t` field if present, else elapsed since first poll.
- Cleans up on unmount or when `url` changes.
- Passing `null` or `undefined` as `url` is a no-op (hook stays idle).

### `LogPanel` Component

```jsx
import { LogPanel } from 'streamator-react'
import 'streamator-react/log.css'   // default styles

<LogPanel logs={logs} active={active} />
```

**All props:**
```jsx
<LogPanel
  logs={logs}                          // required — from useLogStream
  active={active}                      // required — from useLogStream
  waitingText="⏳ Starting…"           // shown while active but no logs yet
  maxHeight="200px"                    // CSS max-height (default: 160px)
  className="my-log"                   // appended to root element class
  style={{}}                           // inline style on root element
  renderEntry={(entry, i) => <div />}  // fully custom entry renderer
/>
```

**Default rendering:**
```
12.3s  🔍 Scraping https://example.com
14.1s  🤖 Evaluating…
15.8s  ✅ Done
```

**Behavior:**
- Returns `null` when not active and no logs
- Shows `waitingText` with pulse animation when active but no logs yet
- Auto-scrolls to latest entry on each new log
- Applies level class to each entry: `log-entry--info`, `log-entry--success`,
  `log-entry--warning`, `log-entry--error`

### `makeFormatEvent(overrides)` Utility

```js
import { makeFormatEvent, BASE_EVENT_LABELS } from 'streamator-react'

const formatEvent = makeFormatEvent({
  scraping: e => `🔍 Scraping ${e.url}`,
  done:     () => `✅ Finished`,
})

const { logs } = useLogStream(url, { formatEvent })
```

`BASE_EVENT_LABELS` covers common events from the existing audible-toolkit packages:
`page_loaded`, `batch_started`, `loading_strategy`, `llm_started`, `llm_done`,
`cache_hit`, `search_started`, `search_done`, `browser_ready`, `retry`.

### Default Styles (`log.css`)

Sensible defaults, fully overridable via CSS custom properties:

```css
/* Theming variables with defaults */
--streamator-bg:           #f8f8f8;
--streamator-border:       #e0e0e0;
--streamator-color:        #444;
--streamator-time-color:   #aaa;
--streamator-radius:       6px;
--streamator-font-size:    0.8rem;
--streamator-max-height:   160px;

/* Level colors */
--streamator-success-color: #2e7d32;
--streamator-warning-color: #f59e0b;
--streamator-error-color:   #c62828;
```

Classes:
- `.streamator-log` — scroll container
- `.streamator-log-time` — timestamp span (tabular-nums)
- `.streamator-log-waiting` — pulsing placeholder
- `.streamator-log-entry` — each row
- `.streamator-log-entry--success/warning/error` — level variants (info has no modifier)

Existing projects using the old `.log` / `.log-time` / `.log-waiting` classes can either:
- Import `streamator-react/log-compat.css` which aliases the old class names, or
- Pass `className="log"` to `LogPanel` and keep their existing stylesheet

### Dependencies

```json
{
  "peerDependencies": { "react": ">=17" }
}
```

No other runtime dependencies.

---

## Migration in audible-toolkit

Once published:

**Python** (`api/streaming.py`):
```python
# Before
class JobLogger: ...   # inline implementation

# After
from streamator import JobLogger
```

**React** — replace three files with one import:
```js
// Before: src/hooks/useLogStream.js + src/components/LogPanel.jsx + src/utils/formatEvent.js

// After
import { useLogStream, LogPanel, makeFormatEvent } from 'streamator-react'
import 'streamator-react/log.css'
```

Matcher and GenreDiscovery can then also adopt `LogPanel` to replace their inline
log rendering (currently duplicated across both pages).
