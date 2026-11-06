from abc import ABC, abstractmethod
from typing import Callable, Optional, Type, Union

from fastcrc import crc16

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
        """Implements data encoding"""

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
        ret = bytearray(data)
        ret.extend(
            (sum(data) % self._modulo).to_bytes(self._byte_width, self._endianness)
        )
        return ret

    def decode(self, data: ByteBufferType) -> ByteBufferType:
        check_sum = data[-self._byte_width :]
        payload = data[: -self._byte_width]
        if int.from_bytes(check_sum, self._endianness) != sum(payload) % self._modulo:
            raise CoderDecodeError("data check-sum does not match")
        return payload


class CRCCoder(Coder):
    """CRCCoder class

    :param method: crc method, defaults to None
    :param endianness: byte's endianess, defaults to "little"
    :raises ValueError: in case of missing method parameter
    """

    _size_by_method = {
        "lte16": 2,
        "ccitt_aug": 2,
    }

    @staticmethod
    def _crc_lte16(data: ByteBufferType) -> int:
        """CRC-16/LTE compatible implementation using fastcrc."""
        return crc16.xmodem(bytes(data))

    @staticmethod
    def _crc_ccitt_aug(data: ByteBufferType) -> int:
        """CRC-16/AUG-CCITT compatible implementation using fastcrc."""
        return crc16.xmodem(bytes(data), 0x1D0F)

    _method_map: dict[str, Callable[[ByteBufferType], int]] = {
        "lte16": _crc_lte16.__func__,
        "ccitt_aug": _crc_ccitt_aug.__func__,
    }

    def __init__(self, method: str = None, endianness: str = "little") -> None:
        """Initializes a new CRCCoder object."""
        if method is None or method not in self._size_by_method:
            raise ValueError("invalid crc calculation method")

        self.method = method
        self._method_callable = self._method_map[method]
        self._crc_size = self._size_by_method[method]
        self._endianness = endianness

    def encode(self, data: ByteBufferType) -> ByteBufferType:
        payload = bytearray(data)
        crc_value = self._method_callable(payload)
        payload.extend(crc_value.to_bytes(self._crc_size, self._endianness))
        return payload

    def decode(self, data: ByteBufferType) -> ByteBufferType:
        crc = int.from_bytes(data[-self._crc_size :], self._endianness)
        payload = data[: -self._crc_size]
        if crc != self._method_callable(payload):
            raise CoderDecodeError("data crc does not match")
        return payload


class CoderStream(
    AsyncChainingStream[ByteListBufferType, ByteListBufferType],
    AsyncByteListIOStream,
):
    """Coder stream class is used to encode or decode data

    :param coder_class: a class to be used for coding and uncoding
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
        """Initializes a CoderStream."""
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

        if decoded_list:
            self._write_output(
                [self._coder.encode(decoded) for decoded in decoded_list]
            )
