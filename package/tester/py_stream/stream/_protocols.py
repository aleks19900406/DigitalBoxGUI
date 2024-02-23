from abc import abstractmethod, abstractproperty
from threading import Condition, Lock, Thread
from typing import Any, Callable, Dict, Optional, Protocol, Type, TypeVar

BT = TypeVar("BT", bound=Any)  # Buffer type
BT2 = TypeVar("BT2", bound=Any)  # Buffer type 2


class StreamType(Protocol):
    """Stream protocol"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

    @abstractproperty
    def is_opened(self) -> bool:
        ...

    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def clear_exceptions(self) -> None:
        ...

    @abstractproperty
    def exceptions(self) -> Dict[str, Exception]:
        ...

    @abstractmethod
    def _check_exception(self) -> None:
        ...


class InputStreamType(StreamType, Protocol[BT]):
    """Input Stream protocol"""

    _BT_I: Type[BT]

    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractproperty
    def in_waiting(self) -> int:
        ...

    @abstractmethod
    def discard(self) -> None:
        ...

    @abstractmethod
    def read(
        self, size: int = 1, block: bool = True, timeout: Optional[float] = None
    ) -> BT:
        ...


class OutputStreamType(StreamType, Protocol[BT]):
    """Output Stream protocol"""

    _BT_O: Type[BT]

    @abstractmethod
    def flush(self) -> None:
        ...

    @abstractmethod
    def write(self, data: BT) -> None:
        ...


class IOStreamType(InputStreamType[BT], OutputStreamType[BT], Protocol[BT]):
    """IO Stream Protocol"""

    ...


class StreamInternalsBaseType(Protocol):
    target: Callable[["StreamInternalsBaseType"], None]
    thread: Optional[Thread]
    buffer_lock: Condition
    exception: Optional[Exception]
    exception_lock: Lock


class AsyncStreamInternalsType(Protocol[BT]):
    buffer: BT
    target: Callable[["AsyncStreamInternalsType[BT]"], None]
    thread: Optional[Thread]
    buffer_lock: Condition
    exception: Optional[Exception]
    exception_lock: Lock

    def __init__(
        self, buffer: BT, target: Callable[["AsyncStreamInternalsType[BT]"], None]
    ) -> None:
        ...


class SyncStreamInternalsType(Protocol[BT]):
    read_buffer: BT
    write_buffer: BT
    target: Callable[["SyncStreamInternalsType[BT]"], None]
    thread: Optional[Thread]
    buffer_lock: Condition
    exception: Optional[Exception]
    exception_lock: Lock

    def __init__(
        self,
        read_buffer: BT,
        write_buffer: BT,
        target: Callable[["SyncStreamInternalsType[BT]"], None],
    ) -> None:
        ...


IT = TypeVar("IT", bound=StreamInternalsBaseType)  #: Internal type
