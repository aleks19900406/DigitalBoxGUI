from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union

from ._protocols import IOStreamType


class StreamStack:
    """StreamStack class is used as a wrapper for a desired chain of streams

    :param stream_params: stacked stream classes with its construction parameters
    :raises ValueError: In case of insufficient number of streams

    Example::

        >>> ss = StreamStack(
        ...     (
        ...         (_SerialStream, ["COM100", 2000000], {}),
        ...         (_PackerStream, [HisensePacker], {}),
        ...         (_CoderStream, [CheckSumCoder], {})
        ...     )
        ... )

    """

    _stack: List[IOStreamType]

    def __init__(
        self,
        stream_params: Sequence[
            Tuple[
                Type[IOStreamType],
                Sequence[Any],
                Dict[str, Any],
            ]
        ],
    ) -> None:
        """Initializes a StreamStack object"""
        stream_class, args, kwargs = stream_params[0]
        self._entry = None
        self._stack = [stream_class(*args, **kwargs)]
        for n, (stream_class, args, kwargs) in enumerate(stream_params[1:]):
            self._stack.append(stream_class(*args, self._stack[n], **kwargs))
        self._entry = self._stack[-1]

    def __del__(self) -> None:
        if self._entry is not None:
            self.close()

    def __getitem__(self, topic):
        return self._entry[topic]

    @property
    def is_opened(self) -> bool:
        """Information about whether a stream stack with underlaying streams is opened
        or not

        :raises RuntimeError: in case the underlying streams does not share the same
                              opened state
        :return: the state of stream stack
        """
        opened = [i.is_opened for i in self._stack]
        if all(opened):
            return True
        elif not any(opened):
            return False
        raise RuntimeError("Not all streams share the same state")

    def open(self) -> None:
        """Opens all streams"""
        self._entry.open()

    def close(self) -> None:
        """Closes all streams"""
        self._entry.close()

    @property
    def in_waiting(self) -> int:
        """Reports the number of objects in waiting

        Not precisely accurate. Probably not suitable for multiple readers.
        """
        return self._entry.in_waiting

    def flush(self) -> None:
        """Same as outer stream's flush"""
        self._entry.flush()

    def discard(self) -> None:
        """Same as outer stream's discard"""
        self._entry.discard()

    def read(
        self, size: int = 1, block: bool = True, timeout: Optional[float] = None
    ) -> Union[bytearray, List[bytearray]]:
        """Same as outer stream's read"""
        return self._entry.read(size, block, timeout)

    def write(self, data: Union[bytearray, List[bytearray]]) -> None:
        """Same as outer stream's write"""
        return self._entry.write(data)

    def clear_exceptions(self) -> None:
        """Clears exceptions on all streams"""
        for stream in self._stack:
            stream.clear_exceptions()

    @property
    def exceptions(self) -> Tuple[Dict[str, Exception]]:
        return tuple(stream.exceptions for stream in self._stack)
