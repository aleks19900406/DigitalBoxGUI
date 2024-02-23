from abc import ABC, abstractmethod
from typing import Optional, Type, Union

import libscrc

from ._base import AsyncChainingStream, AsyncStreamInternals
from ._byte_list import (
    AsyncByteListIOStream,
    ByteListBufferType,
    ByteListInputStreamType,
    ByteListIOStreamType,
    ByteListOutputStreamType,
)
from .byte import ByteBufferType


class CoderError(ValueError):
    """Used for coder"""


class CoderEncodeError(CoderError):
    """Encode error"""


class CoderDecodeError(CoderError):
    """Decode error"""


class Coder(ABC):
    """A coder class used by :class:`tester._common.stream.stream._CoderStream`"""

    def __init__(self, *args, **kwargs) -> None:
        """Allows random construction arguments"""

    @abstractmethod
    def encode(self, data: ByteBufferType) -> ByteBufferType:
        "Implements data encoding"

    @abstractmethod
    def decode(self, data: ByteBufferType) -> ByteBufferType:
        """Implements data decoding"""


class CheckSumCoder(Coder):
    """A checksum coder encodes/decodes given bytes"""

    def __init__(self, byte_width: int = 1, endianess: str = "little") -> None:
        self._byte_width = byte_width
        self._modulo = 2 ** (8 * byte_width)
        self._endianness = endianess
        super().__init__()

    def encode(self, data: ByteBufferType) -> ByteBufferType:
        ret = bytearray([*data])
        ret.extend(
            (sum(data) % self._modulo).to_bytes(self._byte_width, self._endianness)
        )
        return ret

    def decode(self, data: ByteBufferType) -> ByteBufferType:
        check_sum = data[-self._byte_width :]
        data = data[: -self._byte_width]
        if int.from_bytes(check_sum, self._endianness) != sum(data) % self._modulo:
            raise CoderDecodeError("data check-sum does not match")
        return data


class CRCCoder(Coder):
    """CRCCoder class

    :param method: crc method, defaults to None
    :param endianness: byte's endianess, defaults to "little"
    :raises ValueError: in case of missing method parameter
    """

    _size_by_method = {"lte16": 2, "ccitt_aug": 2}

    def __init__(self, method: str = None, endianness: str = "little") -> None:
        """Initializes a new CRCPacker object"""
        if method is None or method not in self._size_by_method:
            raise ValueError("invalid crc calculation method")
        self.method = method
        self._method_callable = getattr(libscrc, method)
        self._crc_size = self._size_by_method[method]
        self._endianness = endianness

    def encode(self, data: bytearray) -> bytearray:
        return bytearray(
            [
                *data,
                *self._method_callable(data).to_bytes(self._crc_size, self._endianness),
            ]
        )

    def decode(self, data: bytearray) -> bytearray:
        crc = int.from_bytes(data[-self._crc_size :], self._endianness)
        data = data[: -self._crc_size]
        if crc != self._method_callable(data):
            raise CoderDecodeError("data crc does not match")
        return data


class CoderStream(
    AsyncChainingStream[ByteListBufferType, ByteListBufferType],
    AsyncByteListIOStream,
):
    """Coder stream class is used to encode or decode data

    :param coder_class: a class to be used for coding anduncoding
    :param input_instance: input stream instance
    :param output_instance: output stream instance. If not passed, the input_instance is
                            used also as an output
    """

    _coder: Coder

    def __init__(
        self,
        coder_class: Type[Coder],
        input_instance: Union[
            ByteListInputStreamType,
            ByteListIOStreamType,
        ],
        output_instance: Optional[ByteListOutputStreamType] = None,
        **kwargs,
    ) -> None:
        """Initializes a _CoderStream"""
        self._coder = coder_class(**kwargs)
        super().__init__(input_instance, output_instance)

    def _read_worker(self, internal: AsyncStreamInternals[ByteListBufferType]) -> None:
        encoded_list = self._read_input()
        decoded_list = [self._coder.decode(encoded) for encoded in encoded_list]
        if decoded_list:
            with internal.buffer_lock:
                internal.buffer.extend(decoded_list)
                internal.buffer_lock.notify_all()

    def _write_worker(self, internal: AsyncStreamInternals[ByteListBufferType]) -> None:
        decoded_list = []
        with internal.buffer_lock:
            internal.buffer_lock.wait()
            if len(internal.buffer):
                decoded_list = internal.buffer[:]
                internal.buffer.clear()
        if len(decoded_list):
            self._write_output(
                [self._coder.encode(decoded) for decoded in decoded_list]
            )
