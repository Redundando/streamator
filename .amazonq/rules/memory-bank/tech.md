# Streamator — Technology Stack

## Languages
- Python ≥ 3.10 (uses `X | Y` union types, match not used)
- JavaScript / JSX (React 17+, no TypeScript)

## Python Package (`python/`)

### Build System
- `setuptools ≥ 68` via `pyproject.toml` (PEP 517)
- Package name: `streamator`, version `0.1.0`

### Runtime Dependencies
- None for core (MemoryStore only)
- `dynamorator ≥ 0.1.6` — optional, for DynamoStore (`pip install streamator[dynamo]`)
- `fastapi ≥ 0.133.1` — optional, for route helpers (`pip install streamator[fastapi]`)

### Dev Dependencies (requirements.txt)
- `pytest ≥ 9.0.2`
- `pytest-asyncio ≥ 1.3.0`
- `httpx` — for FastAPI test client

### Test Configuration
- `asyncio_mode = "auto"` in `pyproject.toml` — all async tests run automatically
- Tests in `python/tests/test_backend.py`

### Key Python APIs Used
- `asyncio.Queue` — MemoryStore push model
- `uuid.uuid4()` — job ID generation
- `time.monotonic()` — elapsed time tracking
- `fastapi.responses.StreamingResponse` — SSE endpoint
- `fastapi.responses.JSONResponse` — error/snapshot responses

## React Package (`react/`)

### Build System
- Rollup 4.x with config in `rollup.config.js`
- Outputs: `dist/index.cjs.js` (CommonJS) + `dist/index.esm.js` (ESM) + `dist/log.css`
- Babel via `@rollup/plugin-babel` with `@babel/preset-react` for JSX
- `@rollup/plugin-node-resolve` for module resolution
- `rollup-plugin-postcss` for CSS bundling

### Peer Dependencies
- `react ≥ 17` (not bundled)

### Dev Dependencies
- `rollup ^4.0.0`
- `@rollup/plugin-node-resolve ^15.0.0`
- `@rollup/plugin-babel ^6.0.0`
- `@babel/core ^7.0.0`
- `@babel/preset-react ^7.0.0`
- `rollup-plugin-postcss ^4.0.0`

### Package Exports
```json
{
  ".": { "import": "./dist/index.esm.js", "require": "./dist/index.cjs.js" },
  "./log.css": "./dist/log.css"
}
```

## Demo App (`demo/`)

### Build System
- Vite 5.x with `@vitejs/plugin-react`
- React 18, react-dom 18
- Consumes `streamator-react` via `file:../react` local path

### Commands
```bash
cd demo && npm run dev    # start Vite dev server
```

## Development Commands

### Python
```bash
cd python
pip install -e ".[fastapi,dynamo]"   # editable install with all extras
pytest                                # run tests
python main.py                        # run local dev server
```

### React Library
```bash
cd react
npm install
npm run build    # rollup -c → dist/
npm run watch    # rollup -c --watch
```

### Demo App
```bash
cd demo
npm install
npm run dev      # vite dev server
```

## Deployment
- EC2-based deployment documented in `EC2_SETUP.md`
- PowerShell scripts: `deploy.ps1`, `setup_ec2.ps1`, `setup_ec2_env.ps1`,
  `setup_streamator_ec2.ps1`, `ssh.ps1`
- Startup: `start.ps1` (Windows) / `start.sh` (Linux)
- Environment variables in `.env` (not committed)
