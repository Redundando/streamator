# Streamator — Development Guidelines

## Code Quality Standards

### Python
- Python ≥ 3.10 features are acceptable: `X | Y` union types in annotations, walrus operator
- Type hints on public method signatures; internal helpers may omit them
- Keep classes small and single-purpose — `JobLogger`, `MemoryStore`, `DynamoStore` are
  each under ~30 lines
- No docstrings in source — code is self-documenting through naming and specs.md
- Raise `ValueError` with an f-string for invalid constructor arguments:
  ```python
  raise ValueError(f"Unknown store: {store!r}")
  ```
- Use `!r` in error messages to show the invalid value clearly

### JavaScript / JSX
- Double quotes for all JS string literals (consistent across all files)
- No semicolons at end of statements — not enforced but not present in source
- Arrow functions for callbacks and short utilities
- Named exports everywhere — no default exports except in demo/main.jsx entry point
- `const` for all module-level declarations; `let` only inside function scope when needed

---

## Structural Conventions

### Python Package Layout
- `__init__.py` exports only the public API — one line per export, `__all__` defined:
  ```python
  from .logger import JobLogger
  __all__ = ["JobLogger"]
  ```
- Optional integrations (fastapi, dynamo) are lazy-loaded inside methods or guarded with
  try/except to avoid hard dependencies:
  ```python
  try:
      from . import fastapi as _fa
      _fa._loggers[self.job_id] = self
  except ImportError:
      pass
  ```
- Optional dependency imports inside class methods (not at module top):
  ```python
  def __init__(self, table: str, ttl_days: float = 7):
      from dynamorator import DynamoDBStore   # lazy import
      self._store = DynamoDBStore(table_name=table)
  ```

### React Package Layout
- `index.js` is a pure re-export barrel — no logic, one export per line:
  ```js
  export { useLogStream } from "./useLogStream.js";
  export { LogPanel } from "./LogPanel.jsx";
  export { makeFormatEvent, BASE_EVENT_LABELS } from "./formatEvent.js";
  ```
- Each file exports exactly one primary thing (hook, component, or utility)
- CSS imported directly in the component file that uses it (`import "./log.css"`)

### Store Interface (informal protocol)
Both stores implement the same interface — no base class, duck typing:
```python
store.append(entry: dict)     # write entry
store.snapshot() -> list      # read all entries
store.close()                 # signal end
store.stream()                # async generator (MemoryStore only)
```

---

## Naming Conventions

### Python
- Private attributes prefixed with `_`: `self._store`, `self._queue`, `self._log`
- Private module-level dicts prefixed with `_`: `_loggers`
- Private functions prefixed with `_`: `_get()`, `_sse_generator()`, `_get()`
- Constructor kwargs use `snake_case`: `ttl_days`, `table`
- Store selection via string key: `"memory"` | `"dynamo"`

### JavaScript
- Hook files: `use` prefix + camelCase noun — `useLogStream.js`
- Component files: PascalCase — `LogPanel.jsx`
- Utility files: camelCase noun — `formatEvent.js`
- CSS class names: BEM-like with `streamator-` prefix:
  - Block: `streamator-log`
  - Element: `streamator-log-entry`, `streamator-log-time`, `streamator-log-waiting`
  - Modifier: `streamator-log-entry--success`, `streamator-log-entry--error`
- CSS custom properties: `--streamator-{property}` pattern

---

## Semantic Patterns

### Log Entry Shape
Canonical entry object used throughout both packages:
```python
# Python (produced by logger.log())
{"event": "log", "message": "...", "level": "info", "t": 1.23}
```
```js
// React (consumed by useLogStream, rendered by LogPanel)
{ text: "...", level: "info", t: "1.2s" }
```
`t` is always a float (seconds) on the wire; formatted to `"1.2s"` string client-side.

### Log Levels
Four levels only: `"info"` | `"success"` | `"warning"` | `"error"`.
`"info"` is the default and gets no CSS modifier class (others get `--{level}` suffix).

### SSE Pattern
```python
# Server: yield newline-delimited SSE frames
async def _sse_generator(logger):
    async for entry in logger._store.stream():
        yield f"data: {json.dumps(entry)}\n\n"
```
```js
// Client: parse JSON from e.data, check for done sentinel
es.onmessage = (e) => {
  const raw = JSON.parse(e.data);
  if (raw.event === "done") { setActive(false); es.close(); return; }
  ...
};
```

### Poll Pattern
```js
// Slice from last seen index to get only new entries
const newEntries = all.slice(seen).map((raw) => toEntry(raw, elapsed));
seen = all.length;
```

### formatEvent Override Pattern
```js
// Merge caller overrides on top of base labels
const labels = { ...BASE_EVENT_LABELS, ...overrides };
return (raw) => {
  const fn = labels[raw.event];
  if (fn) return fn(raw);
  return raw.message ?? null;   // null suppresses the entry
};
```

### React Hook Cleanup
Always return a cleanup function from useEffect that closes connections and resets state:
```js
return () => { es.close(); setActive(false); };
```

### Null-guard for URL
Hook is a no-op when url is falsy — check at top of useEffect:
```js
if (!url) return;
```

### CSS Class Merging
Filter out falsy values before joining class names:
```jsx
className={["streamator-log", className].filter(Boolean).join(" ")}
```

### maxHeight via CSS Custom Property
Pass maxHeight as a CSS custom property on the style object, not as a direct style:
```jsx
const rootStyle = maxHeight
  ? { ...style, "--streamator-max-height": maxHeight }
  : style;
```

### Auto-scroll Pattern
```jsx
const bottomRef = useRef(null);
useEffect(() => {
  bottomRef.current?.scrollIntoView({ behavior: "smooth" });
}, [logs]);
// Render: <div ref={bottomRef} /> at end of list
```

---

## Build & Config Patterns

### Rollup (react library)
- `external: ["react", "react/jsx-runtime"]` — never bundle peer deps
- Dual output: ESM + CJS in a single config array
- CSS extracted to a separate file via `postcss({ extract: "log.css" })`
- Babel with `runtime: "automatic"` — no need to import React in JSX files

### Vite (demo)
- Alias `streamator-react` to `../react/src/index.js` for live dev without building:
  ```js
  resolve: { alias: { "streamator-react": path.resolve("../react/src/index.js") } }
  ```
- Proxy `/api` to backend server for local dev

### pyproject.toml
- `asyncio_mode = "auto"` under `[tool.pytest.ini_options]` — no `@pytest.mark.asyncio`
  decorator needed on individual tests
- Optional deps declared as extras: `[dynamo]` and `[fastapi]`

---

## AI Documentation
The `python/.ai-docs/` directory contains markdown reference docs for key dependencies
(`dynamorator`, `fastapi`, `pytest-asyncio`, `pytest`). Add new dependency docs here
when introducing new libraries so AI tools have accurate API context.
