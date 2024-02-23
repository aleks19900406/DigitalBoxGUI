from abc import abstractmethod
from dataclasses import dataclass, field
from threading import Condition, Event, Lock, Thread
from time import sleep
from typing import Callable, Dict, Generic, Literal, Optional, Type, Union, cast

from ._protocols import (
    BT,
    BT2,
    IT,
    AsyncStreamInternalsType,
    InputStreamType,
    IOStreamType,
    OutputStreamType,
    SyncStreamInternalsType,
)
from ._utils import Timer, check_opened


class StreamBase(Generic[IT]):
    """Threaded stream base class"""

    _internals: Dict[str, IT]

    def __init__(self) -> None:
        """Initializes _Stream object"""
        self._should_stop = Event()
        self._should_stop.set()
        self._internals = {}

    def __del__(self) -> None:
        self.close()

    @property
    def is_opened(self) -> bool:
        """Whether a stream is opened or not"""
        return not self._should_stop.is_set()

    def _open_begin(self) -> None:
        """Override to execute some code before actually opening stream"""

    def _open_finalize(self) -> None:
        """Override to execute some code just after opening stream"""

    def open(self) -> None:
        """Opens stream

        :raises RuntimeError: in case the stream is already opened
        """
        if self.is_opened:
            raise RuntimeError("stream is already open")
        self.clear_exceptions()
        self._should_stop.clear()
        self._open_begin()
        for key, internal in self._internals.items():
            internal.thread = Thread(
                target=self._worker,
                args=(internal,),
                daemon=True,
                name=f"{self.__class__.__name__}-{key}",
            )
            internal.thread.start()
        self._open_finalize()

    def _close_begin(self) -> None:
        """Override to execute some code before actually closing stream"""

    def _close_finalize(self) -> None:
        """Override to execute some code just after opening stream"""

    def close(self) -> None:
        """Closes a stream"""
        self._should_stop.set()
        self._close_begin()
        for internal in self._internals.values():
            with internal.buffer_lock:
                internal.buffer_lock.notify_all()
            if internal.thread is not None:
                internal.thread.join()
                internal.thread = None
        self._close_finalize()

    def _worker(self, internal: IT) -> None:
        while not self._should_stop.is_set():
            try:
                internal.target(internal)
            except Exception as ex:
                self._should_stop.set()
                with internal.exception_lock:
                    internal.exception = ex
                with internal.buffer_lock:
                    internal.buffer_lock.notify_all()

    def _check_exception(self) -> None:
        """Check if any thread raised an exception

        :raises Exception: in case any thread caught an exception
        """
        for key, internal in self._internals.items():
            with internal.exception_lock:
                exception = internal.exception
            if exception is not None:
                raise type(exception)(
                    f'"{key}" internal of {self.__class__.__name__} '
                    f"encountered an error: {exception}"
                )

    def clear_exceptions(self) -> None:
        """Clears exceptions"""
        for internal in self._internals.values():
            with internal.exception_lock:
                internal.exception = None

    @property
    def exceptions(self) -> Dict[str, Exception]:
        exceptions: Dict[str, Exception] = {}
        for key, internal in self._internals.items():
            with internal.exception_lock:
                exception = internal.exception
            if exception is not None:
                exceptions[key] = exception
        return exceptions


@dataclass
class AsyncStreamInternals(Generic[BT]):
    buffer: BT
    target: Callable[["AsyncStreamInternals[BT]"], None]
    thread: Optional[Thread] = None
    buffer_lock: Condition = field(default_factory=Condition)
    exception: Optional[Exception] = None
    exception_lock: Lock = field(default_factory=Lock)


class AsyncInputInternals(Dict, Generic[BT]):
    def __getitem__(self, index: Literal["read"]) -> AsyncStreamInternals[BT]:
        ...


class AsyncOutputInternals(Dict, Generic[BT]):
    def __getitem__(self, index: Literal["write"]) -> AsyncStreamInternals[BT]:
        ...


class AsyncIOInternals(Dict, Generic[BT]):
    def __getitem__(
        self, index: Union[Literal["write"], Literal["read"]]
    ) -> AsyncStreamInternals[BT]:
        ...


class AsyncInputStream(
    StreamBase[AsyncStreamInternalsType[BT]], InputStreamType, Generic[BT]
):
    """Input stream class"""

    _BT_I: Type[BT]
    _IT_I: Type[AsyncStreamInternalsType[BT]]
    _internals: AsyncInputInternals[BT]

    def __init__(self) -> None:
        super().__init__()
        self._internals["read"] = self._IT_I(self._BT_I(), self._read_worker)

    def __len__(self) -> int:
        internal = self._internals["read"]
        with internal.buffer_lock:
            return len(internal.buffer)

    @property
    def in_waiting(self) -> int:
        """Reports the number of objects in waiting

        Not precisely accurate. Probably not suitable for multiple readers.
        """
        return self.__len__()

    @abstractmethod
    def _read_worker(self, internal: AsyncStreamInternalsType[BT]) -> None:
        """Reader implementation"""

    def _discard_impl(self, internal: AsyncStreamInternalsType[BT]) -> None:
        """Discard implementation"""
        with internal.buffer_lock:
            internal.buffer.clear()

    @check_opened
    def discard(self) -> None:
        """Discards data in read buffer"""
        self._discard_impl(self._internals["read"])

    @check_opened
    def read(
        self, size: int = 1, block: bool = True, timeout: Optional[float] = None
    ) -> BT:
        """Read from the stream

        :param size: number of data objects to read
        :param block: whether the read should block, defaults to True
        :param timeout: timeout to be applied on blocking read, defaults to None
        :return: any sequence container of any object
        """
        result = self._BT_I()
        to_read = size
        internal = self._internals["read"]
        with Timer(timeout) as timer:
            while True:
                self._check_exception()
                with internal.buffer_lock:
                    if len(internal.buffer):
                        result.extend(internal.buffer[:to_read])
                        internal.buffer = internal.buffer[to_read:]
                        to_read = size - len(result)
                    if not to_read:
                        break
                    if block:
                        internal.buffer_lock.wait(timer.remaining)
                        if not len(internal.buffer):
                            break
                if timer.expired or not block:
                    break
                sleep(0)
        self._check_exception()
        return result


class AsyncOutputStream(
    StreamBase[AsyncStreamInternalsType[BT]], OutputStreamType, Generic[BT]
):
    """Threaded output stream class"""

    _BT_O: Type[BT]
    _IT_O: Type[AsyncStreamInternalsType[BT]]
    _internals: AsyncOutputInternals[BT]

    def __init__(self) -> None:
        super().__init__()
        self._internals["write"] = self._IT_O(self._BT_O(), self._write_worker)

    @check_opened
    def flush(self) -> None:
        """Flushes outgoing data"""
        internal = self._internals["write"]
        while len(internal.buffer):
            sleep(0)

    @abstractmethod
    def _write_worker(self, internal: AsyncStreamInternalsType[BT]) -> None:
        """Writer implementation"""

    @check_opened
    def write(self, data: BT) -> None:
        """Write to the stream

        :param data: data to be written to stream
        """
        self._check_exception()
        internal = self._internals["write"]
        with internal.buffer_lock:
            internal.buffer.extend(data)
            internal.buffer_lock.notify_all()
        self._check_exception()


class AsyncIOStream(AsyncInputStream[BT], AsyncOutputStream[BT], IOStreamType):
    """Input/output stream base class"""

    _internals: AsyncIOInternals[BT]


@dataclass
class SyncStreamInternals(Generic[BT]):
    read_buffer: BT
    write_buffer: BT
    target: Callable[["SyncStreamInternals[BT]"], None]
    thread: Optional[Thread] = None
    buffer_lock: Condition = field(default_factory=Condition)
    exception: Optional[Exception] = None
    exception_lock: Lock = field(default_factory=Lock)


class SyncIOInternals(Dict, Generic[BT]):
    def __getitem__(self, index: Literal["r_w"]) -> SyncStreamInternals[BT]:
        ...


class SyncIOStream(StreamBase[BT], IOStreamType):
    _BT_I: Type[BT]
    _BT_O: Type[BT]
    _IT_I_O: Type[SyncStreamInternalsType[BT]]
    _internals: SyncIOInternals[BT]

    def __init__(self) -> None:
        super().__init__()
        self._internals["r_w"] = self._IT_I_O(
            self._BT_I(), self._BT_O(), self._r_w_worker
        )

    def __len__(self) -> int:
        internal = self._internals["r_w"]
        with internal.buffer_lock:
            return len(internal.read_buffer)

    @property
    def in_waiting(self) -> int:
        return self.__len__()

    def _discard_impl(self, internal: SyncStreamInternals[BT]) -> None:
        with internal.buffer_lock:
            internal.read_buffer.clear()

    @check_opened
    def discard(self) -> None:
        self._discard_impl(self._internals["r_w"])

    @check_opened
    def flush(self) -> None:
        internal = self._internals["r_w"]
        while len(internal.write_buffer):
            sleep(0)

    @abstractmethod
    def _r_w_worker(self, internal: SyncStreamInternalsType[BT]):
        ...

    @check_opened
    def read(
        self, size: int = 1, block: bool = True, timeout: Optional[float] = None
    ) -> BT:
        result = self._BT_I()
        to_read = size
        internal = self._internals["r_w"]
        with Timer(timeout) as timer:
            while True:
                self._check_exception()
                with internal.buffer_lock:
                    if len(internal.read_buffer):
                        result.extend(internal.read_buffer[:to_read])
                        internal.read_buffer = internal.read_buffer[to_read:]
                        to_read = size - len(result)
                    if not to_read:
                        break
                    if block:
                        internal.buffer_lock.wait(timer.remaining)
                        if not len(internal.read_buffer):
                            break
                if timer.expired or not block:
                    break
                sleep(0)
        self._check_exception()
        return result

    @check_opened
    def write(self, data: BT) -> None:
        self._check_exception()
        internal = self._internals["r_w"]
        with internal.buffer_lock:
            internal.write_buffer.extend(data)
            internal.buffer_lock.notify_all()
        self._check_exception()


class ChainingStream(IOStreamType[BT], Generic[BT, BT2]):
    """_ChainingStream base class is a stream that could be chained on top of another
    stream

    :param input_instance: stream to read from
    :param output_instance: stream to write rom, if None, the input_instance is used
    """

    _input: InputStreamType[BT2]
    _output: OutputStreamType[BT2]

    def __init__(
        self,
        input_instance: Union[InputStreamType[BT2], IOStreamType[BT2]],
        output_instance: Optional[OutputStreamType[BT2]] = None,
    ) -> None:
        self._input = input_instance
        self._output = (
            cast(OutputStreamType, input_instance)
            if output_instance is None
            else output_instance
        )

    def _open_begin(self) -> None:
        self._input.open()
        if not self._input is self._output:
            self._output.open()

    def _close_begin(self) -> None:
        self._input.close()
        if not self._input is self._output:
            self._output.close()

    def _read_input(self) -> BT2:
        """Reads data from connected input

        :return: returns read data
        """
        return self._input.read(self._input.in_waiting or 1)

    def _write_output(self, data: BT2) -> None:
        """Writes data to connected output

        :param data: data to be written to output
        :return: number of objects written - in case if timeout on write is used
        """
        return self._output.write(data)


class AsyncChainingStream(ChainingStream[BT, BT2], AsyncIOStream[BT]):
    def __init__(
        self,
        input_instance: Union[InputStreamType[BT2], IOStreamType[BT2]],
        output_instance: Optional[OutputStreamType[BT2]],
    ) -> None:
        ChainingStream.__init__(self, input_instance, output_instance=output_instance)
        AsyncIOStream.__init__(self)

    def flush(self):
        AsyncIOStream.flush(self)
        self._output.flush()


class SyncChainingStream(ChainingStream[BT, BT2], SyncIOStream[BT]):
    def __init__(
        self,
        input_instance: Union[InputStreamType[BT2], IOStreamType[BT2]],
        output_instance: Optional[OutputStreamType[BT2]] = None,
    ) -> None:
        ChainingStream.__init__(self, input_instance, output_instance=output_instance)
        SyncIOStream.__init__(self)

    def flush(self) -> None:
        SyncIOStream.flush(self)
        self._output.flush()
