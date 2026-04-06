from dataclasses import dataclass
from threading import Lock
from typing import Dict


@dataclass
class _MutableState:
    unbound_cleared: bool = False
    redis_cleared: bool = False
    last_action: str = "none"


class AppState:
    def __init__(self) -> None:
        self._state = _MutableState()
        self._lock = Lock()

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            return {
                "unbound_cleared": self._state.unbound_cleared,
                "redis_cleared": self._state.redis_cleared,
                "last_action": self._state.last_action,
            }

    def mark_unbound_cleared(self, action: str) -> None:
        with self._lock:
            self._state.unbound_cleared = True
            self._state.last_action = action

    def mark_redis_cleared(self, action: str) -> None:
        with self._lock:
            self._state.redis_cleared = True
            self._state.last_action = action

    def mark_after_successful_local_resolve(self) -> None:
        with self._lock:
            self._state.unbound_cleared = False
            if self._state.redis_cleared:
                self._state.redis_cleared = False
