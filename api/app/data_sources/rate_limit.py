from __future__ import annotations

import threading
import time


class RateLimiter:
    def __init__(self, minimum_interval: float) -> None:
        self.minimum_interval = minimum_interval
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self) -> None:
        with self._lock:
            remaining = self.minimum_interval - (time.monotonic() - self._last_call)
            if remaining > 0:
                time.sleep(remaining)
            self._last_call = time.monotonic()
