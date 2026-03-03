import asyncio
import time
import warnings

from .logger import JobLogger

_emitters: dict[str, "JobEmitter"] = {}
_results: dict[str, object] = {}


class JobEmitter:
    def __init__(self, store="memory", **kwargs):
        self._logger = JobLogger(store=store, **kwargs)
        self._closed = False
        self._task = None
        _emitters[self.job_id] = self

    @property
    def job_id(self) -> str:
        return self._logger.job_id

    def emit(self, event: dict):
        if self._closed:
            warnings.warn(f"emit() called after close() on job {self.job_id!r}", stacklevel=2)
            return
        entry = {**event, "t": round(time.monotonic() - self._logger.start_t, 3)}
        self._logger._store.append(entry)

    def log(self, message: str, level: str = "info"):
        if self._closed:
            warnings.warn(f"log() called after close() on job {self.job_id!r}", stacklevel=2)
            return
        self._logger.log(message, level=level)

    def track(self, task):
        self._task = task

    def set_result(self, data):
        _results[self.job_id] = data

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._logger.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        self.close()

    @classmethod
    def cancel(cls, job_id: str):
        emitter = _emitters.get(job_id)
        if emitter and emitter._task:
            emitter._task.cancel()

    @classmethod
    def pop_result(cls, job_id: str):
        return _results.pop(job_id, None)

    @classmethod
    def exists(cls, job_id: str) -> bool:
        return job_id in _emitters


async def start_reaper(ttl_seconds: int = 300, interval: int = 60):
    while True:
        await asyncio.sleep(interval)
        cutoff = time.monotonic()
        expired = [
            jid for jid, e in list(_emitters.items())
            if e._closed and (cutoff - e._logger.start_t) > ttl_seconds
        ]
        for jid in expired:
            JobEmitter.cancel(jid)
            _emitters.pop(jid, None)
            _results.pop(jid, None)
