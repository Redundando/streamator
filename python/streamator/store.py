import asyncio


class MemoryStore:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._log = []
        self._closed = False

    def append(self, entry: dict):
        self._log.append(entry)
        self._queue.put_nowait(entry)

    async def stream(self):
        while True:
            entry = await self._queue.get()
            if entry is None:
                break
            yield entry

    def snapshot(self) -> list:
        return list(self._log)

    def close(self):
        self._closed = True
        self._queue.put_nowait(None)


class DynamoStore:
    def __init__(self, table: str, ttl_days: float = 7):
        from dynamorator import DynamoDBStore
        self._store = DynamoDBStore(table_name=table)
        self._ttl_days = ttl_days
        self._key = None
        self._closed = False

    def set_key(self, job_id: str):
        self._key = job_id

    def append(self, entry: dict):
        existing = self._store.get(self._key) or {"logs": []}
        existing["logs"].append(entry)
        self._store.put(self._key, existing, ttl_days=self._ttl_days)

    def close(self):
        self._closed = True

    def snapshot(self) -> list:
        data = self._store.get(self._key)
        return data["logs"] if data else []
