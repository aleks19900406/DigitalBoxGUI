from collections import defaultdict
from ctypes import ArgumentError
from dataclasses import dataclass, field
from threading import Condition, Lock, Thread
from time import sleep
from typing import (
    Callable,
    DefaultDict,
    Dict,
    Generic,
    Hashable,
    List,
    Literal,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from ._base import AsyncChainingStream, AsyncStreamInternals, ChainingStream
from ._list import ListIOStreamType
from ._protocols import BT, BT2, InputStreamType, IOStreamType, OutputStreamType
from ._utils import Timer, check_opened

TT = TypeVar("TT", bound=Hashable)


class _Topic(ListIOStreamType[BT], Generic[TT, BT, BT2]):
    _stream: ChainingStream[DefaultDict[TT, List[BT]], List[BT2]]
    _topic: TT
    _i_buffer_lock: Condition
    _i_buffer: Dict[TT, List[BT]]
    _i_order: List[TT]
    _o_buffer_lock: Condition
    _o_buffer: Dict[TT, List[BT]]
    _o_order: List[TT]

    def __del__(self):
        """Don't close anything"""

    def open(self) -> None:
        raise RuntimeError("invalid operation. Open may be called on parent stream")

    def close(self) -> None:
        raise RuntimeError("invalid operation. Close may be called on parent stream")

    @property
    def is_opened(self):
        return self._stream.is_opened

    def __len__(self) -> int:
        with self._i_buffer_lock:
            return len(self._i_buffer[self._topic])

    @property
    def in_waiting(self) -> int:
        return self.__len__()

    def flush(self) -> None:
        while self._o_buffer[self._topic]:
            sleep(0)

    def discard(self) -> None:
        with self._i_buffer_lock:
            indexes = (n for n, i in enumerate(self._o_order) if i == self._topic)
            for i in indexes:
                del self._i_order[i]
            self._i_buffer[self._topic].clear()

    def _check_exception(self) -> None:
        return self._stream._check_exception()

    @property
    def exceptions(self) -> Dict[str, Exception]:
        return self._stream.exceptions

    def clear_exceptions(self) -> None:
        raise RuntimeError(
            "invalid operation. Exceptions may be cleared on parent stream"
        )

    @check_opened
    def read(
        self, size: int = 1, block: bool = True, timeout: Optional[float] = None
    ) -> List[BT]:
        """Read a topic stream

        :param size: number of data objects to read, defaults to 1
        :param block: whether the read should block, defaults to True
        :param timeout: timeout to be applied on blocking read, defaults to None
        :return: list of data objects
        """
        result = []
        to_read = size
        with Timer(timeout) as timer:
            self._check_exception()
            while not timer.expired:
                with self._i_buffer_lock:
                    if len(self._i_buffer[self._topic]):
                        result += self._i_buffer[self._topic][:to_read]
                        self._i_buffer[self._topic] = self._i_buffer[self._topic][
                            to_read:
                        ]
                        to_read = size - len(result)
                    if not to_read:
                        break
                    if block:
                        self._i_buffer_lock.wait(timer.remaining)
                        # May be triggered multiple times by other topics
                    else:
                        break
                if timer.expired or not block:
                    break
                sleep(0)
        for _ in result:
            with self._i_buffer_lock:
                self._i_order.remove(self._topic)
        self._check_exception()
        return result

    @check_opened
    def write(self, data: List[BT]) -> None:
        """Write a topic stream

        :param data: data to be written to stream
        """
        self._check_exception()
        with self._o_buffer_lock:
            self._o_order.extend([self._topic] * len(data))
            self._o_buffer[self._topic].extend(data)
            self._o_buffer_lock.notify_all()


class AsyncTopicStreamInternalsType(Protocol[TT, BT]):
    buffer: DefaultDict[TT, List[BT]]
    target: Callable[["AsyncTopicStreamInternalsType[TT, BT]"], None]
    thread: Optional[Thread]
    buffer_lock: Condition
    exception: Optional[Exception]
    exception_lock: Lock
    order: List[TT]

    def __init__(
        self,
        buffer: BT,
        target: Callable[["AsyncTopicStreamInternalsType[TT, BT]"], None],
    ) -> None:
        ...


@dataclass
class AsyncTopicStreamInternals(
    AsyncStreamInternals[DefaultDict[TT, List[BT]]], Generic[TT, BT]
):
    order: List[TT] = field(default_factory=list)


class AsyncTopicIOInternals(Dict, Generic[TT, BT]):
    def __getitem__(
        self, k: Union[Literal["read"], Literal["write"]]
    ) -> AsyncTopicStreamInternals[TT, BT]:

        ...


class _TopicStreamBuffer(Generic[TT, BT]):
    def __new__(cls) -> DefaultDict[TT, List[BT]]:
        return defaultdict(list)


class AsyncTopicIOStream(
    AsyncChainingStream[DefaultDict[TT, List[BT]], BT2],
    Generic[TT, BT, BT2],
):

    _BT_I: Type[_TopicStreamBuffer[TT, BT]] = _TopicStreamBuffer[TT, BT]
    _BT_O: Type[_TopicStreamBuffer[TT, BT]] = _TopicStreamBuffer[TT, BT]
    _TT_I: Type[TT]
    _IT_I: Type[AsyncTopicStreamInternalsType[TT, BT]]
    _TT_O: Type[TT]
    _IT_O: Type[AsyncTopicStreamInternalsType[TT, BT]]
    _internals: AsyncTopicIOInternals[TT, BT]

    def __getitem__(self, topic: TT) -> "_AsyncTopic[TT, BT, BT2]":
        return _AsyncTopic[TT, BT, BT2](self, topic)

    def __len__(self) -> int:
        internal = self._internals["read"]
        with internal.buffer_lock:
            return len(internal.order)

    def _discard_impl(self, internal: AsyncTopicStreamInternalsType[TT, BT]) -> None:
        with internal.buffer_lock:
            internal.order.clear()
            internal.buffer.clear()

    @check_opened
    def flush(self) -> None:
        """Flushes data on all outgoing topics"""
        internal = self._internals["write"]
        while any([len(queue) for queue in internal.buffer.values()]):
            sleep(0)
        self._output.flush()

    @check_opened
    def read(
        self, size: int = 1, block: bool = True, timeout: Optional[float] = None
    ) -> List[Tuple[TT, BT]]:
        result: List[Tuple[TT, BT]] = []
        to_read = size
        internal = self._internals["read"]
        with Timer(timeout) as timer:
            while not timer.expired:
                self._check_exception()
                with internal.buffer_lock:
                    if len(internal.order):
                        topics = internal.order[:to_read]
                        internal.order = internal.order[to_read:]
                        for topic in topics:
                            result.append((topic, internal.buffer[topic].pop(0)))
                        to_read = size - len(result)
                    if not to_read:
                        break
                    if block:
                        internal.buffer_lock.wait(timer.remaining)
                        if not len(internal.order):
                            break
                if timer.expired or not block:
                    break
                sleep(0)
        self._check_exception()
        return result

    @check_opened
    def write(self, data: List[Tuple[TT, BT]]) -> None:
        self._check_exception()
        internal = self._internals["write"]
        for topic, message in data:
            topic = self._TT_O(topic)  # ensure hashable
            with internal.buffer_lock:
                internal.order.append(topic)
                internal.buffer[topic].append(message)
                internal.buffer_lock.notify_all()


class _AsyncTopic(_Topic[TT, BT, BT2]):
    def __init__(self, stream: "AsyncTopicIOStream[TT, BT, BT2]", topic: TT) -> None:
        self._stream = stream
        self._topic = stream._TT_I(topic)  # ensure hashable
        internal = stream._internals["read"]
        self._i_buffer_lock = internal.buffer_lock
        self._i_buffer = internal.buffer
        self._i_order = internal.order
        internal = stream._internals["write"]
        self._o_buffer_lock = internal.buffer_lock
        self._o_buffer = internal.buffer
        self._o_order = internal.order


class ByteTopicStream(
    AsyncTopicIOStream[bytes, bytearray, List[bytearray]],
):
    _IT_I = AsyncTopicStreamInternals[bytes, bytearray]
    _IT_O = AsyncTopicStreamInternals[bytes, bytearray]
    _TT_I = bytes
    _TT_O = bytes

    def __init__(
        self,
        input_instance: Union[InputStreamType[BT2], IOStreamType[BT2]],
        output_instance: Optional[OutputStreamType[BT2]] = None,
        topic_length: int = None,
    ) -> None:
        if topic_length is None:
            raise ArgumentError("topic_length argument missing")
        super().__init__(input_instance, output_instance=output_instance)
        self._topic_length = topic_length

    def __getitem__(
        self, topic: bytes
    ) -> "_AsyncTopic[bytes, bytearray, List[bytearray]]":
        if len(topic) != self._topic_length:
            raise ValueError("invalid topic length")
        return super().__getitem__(topic)

    def _read_worker(
        self, internal: AsyncTopicStreamInternals[bytes, bytearray]
    ) -> None:
        packets = self._read_input()
        for packet in packets:
            topic = bytes(packet[: self._topic_length])  # Ensure hashable
            data = packet[self._topic_length :]
            with internal.buffer_lock:
                internal.order.append(topic)
                internal.buffer[topic].append(data)
                internal.buffer_lock.notify_all()
            sleep(0)

    def _write_worker(
        self, internal: AsyncTopicStreamInternals[bytes, bytearray]
    ) -> None:
        with internal.buffer_lock:
            internal.buffer_lock.wait()
            while internal.order:
                topic = internal.order.pop(0)
                data = internal.buffer[topic].pop(0)
                internal.buffer_lock.release()
                self._output.write([bytearray(topic + data)])
                internal.buffer_lock.acquire()
