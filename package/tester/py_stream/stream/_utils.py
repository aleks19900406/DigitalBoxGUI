from functools import wraps
from time import time
from typing import Any, Callable, Optional, Protocol, TypeVar, cast

from ._protocols import StreamType

F = TypeVar("F", bound=Callable[..., Any])


def check_opened(f: F) -> F:
    @wraps(f)
    def wrapper(self: StreamType, *args, **kwargs):
        if not self.is_opened:
            raise RuntimeError("stream is not opened")
        return f(self, *args, **kwargs)

    return cast(F, wrapper)


class Timer:
    """Timer object, used for timing blocking operations

    :param duration: desired timer's duration
    """

    def __init__(self, duration: Optional[float]) -> None:
        """Initializes _Timer object"""
        self._t_stop = time() + duration if duration is not None else duration

    def __enter__(self) -> "Timer":
        """Enables with ... support"""
        return self

    def __exit__(self, *args, **kwargs) -> None:
        """Enables with ... support"""
        pass

    @property
    def remaining(self) -> Optional[float]:
        """Timer's remaining time"""
        if self._t_stop is None:
            return None
        else:
            remaining = self._t_stop - time()
            return remaining if remaining > 0 else 0

    @property
    def expired(self) -> bool:
        """Whether the timer is expired or not"""
        return self._t_stop is not None and (time() - self._t_stop) >= 0
