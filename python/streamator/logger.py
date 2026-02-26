import time
import uuid

from .store import MemoryStore, DynamoStore


class JobLogger:
    def __init__(self, store="memory", **kwargs):
        self.job_id = str(uuid.uuid4())
        self.start_t = time.monotonic()

        if store == "memory":
            self._store = MemoryStore()
        elif store == "dynamo":
            self._store = DynamoStore(
                table=kwargs["table"],
                ttl_days=kwargs.get("ttl_days", 7),
            )
            self._store.set_key(self.job_id)
        else:
            raise ValueError(f"Unknown store: {store!r}")

        try:
            from . import fastapi as _fa
            _fa._loggers[self.job_id] = self
        except ImportError:
            pass

    def log(self, message: str, level: str = "info"):
        entry = {
            "event": "log",
            "message": message,
            "level": level,
            "t": round(time.monotonic() - self.start_t, 3),
        }
        self._store.append(entry)

    def close(self):
        self._store.close()

