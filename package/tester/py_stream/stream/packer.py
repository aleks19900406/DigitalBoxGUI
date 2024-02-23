from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from threading import Condition
from typing import AnyStr, Optional, Sequence, Type, Union

from ._base import AsyncChainingStream, AsyncStreamInternals
from ._byte_list import (
    AsyncByteListInputStream,
    AsyncByteListIOStream,
    ByteListBufferType,
    ByteListInternalsType,
)
from .byte import (
    ByteBufferType,
    ByteInputStreamType,
    ByteIOStreamType,
    ByteOutputStreamType,
)


class Packer(ABC):
    """A packer class used by :class:`tester._common.stream.stream._PackerStream`"""

    def __init__(
        self,
        *args,
        out_of_packet_stream: Optional["OutOfPacketStream"] = None,
        **kwargs,
    ) -> None:
        """Allows random construction arguments

        :param out_of_packet_stream: stream to be used to send out of packet data to.
        """
        self._out_of_packet_stream = out_of_packet_stream

    @abstractmethod
    def pack_data(self, data: ByteBufferType) -> ByteBufferType:
        """Implements data packing"""

    @abstractmethod
    def try_unpack_data(self, packet: ByteBufferType) -> ByteListBufferType:
        """Implements data unpacking"""

    def handle_out_of_packet_data(self, data: int) -> None:
        """Implements desired out of packet data manipulation"""
        if self._out_of_packet_stream is not None:
            self._out_of_packet_stream.put(data)


class TerminationPacker(Packer):
    """A termination packer splits incoming bytestream into packages based on
    given terminator

    :param terminator: desired terminator to split bytes at, defaults to b"\n"
    """

    def __init__(self, terminator: Union[AnyStr, Sequence[int]] = b"\n") -> None:
        """Initializes a new TerminationPacker object"""
        super().__init__()
        self._packet = bytearray()
        if isinstance(terminator, str):
            self.terminator = bytearray(terminator, "utf-8")
        else:
            self.terminator = bytearray(terminator)

    def pack_data(self, data: ByteBufferType) -> ByteBufferType:
        if self.terminator in data:
            raise ValueError("data argument should not be already terminated")
        return bytearray([*data, *self.terminator])

    def try_unpack_data(self, packet: ByteBufferType) -> ByteListBufferType:
        self._packet.extend(packet)
        packets = self._packet.split(self.terminator)
        self._packet = packets.pop()
        return packets


class StuffingPacker(Packer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._packet = bytearray()
        self._in_packet = False
        self._previous_byte = 0


class HisensePacker(StuffingPacker):
    """A Hisense packer splits incoming bytestream into packages based on given
    terminator
    """

    ESCAPE = 0xF4
    START = 0xF5
    STOP = 0xFB

    def pack_data(self, data: ByteBufferType) -> ByteBufferType:
        packet = data.replace(
            bytearray([self.ESCAPE]), bytearray([self.ESCAPE, self.ESCAPE])
        )
        return bytearray([self.ESCAPE, self.START, *packet, self.ESCAPE, self.STOP])

    def try_unpack_data(self, packet: ByteBufferType) -> ByteListBufferType:
        packets = []
        for current_byte in packet:
            if self._previous_byte == self.ESCAPE:
                self._previous_byte = 0  # Anything but escape
                if current_byte == self.START:
                    self._packet = bytearray()
                    self._in_packet = True
                elif current_byte == self.ESCAPE:
                    self._packet.append(current_byte)
                elif current_byte == self.STOP:
                    if self._in_packet:
                        self._in_packet = False
                        packets.append(self._packet)
                else:
                    self._in_packet = False
                    for b in self._packet:
                        self.handle_out_of_packet_data(b)
            elif current_byte == self.ESCAPE:
                self._previous_byte = current_byte
            elif self._in_packet:
                self._packet.append(current_byte)
            else:
                self.handle_out_of_packet_data(current_byte)
        return packets


class InspectorPacker(StuffingPacker):
    """Inspector packer"""

    SOF = 0xFD
    EOF = 0xFE
    STF = 0xFF

    def pack_data(self, data: ByteBufferType) -> ByteBufferType:
        packed = bytearray([self.SOF])
        for byte in data:
            if byte < self.SOF:
                packed.append(byte)
            else:
                packed.extend([self.STF, self.STF - byte])
        packed.append(self.EOF)
        return packed

    def try_unpack_data(self, packet: ByteBufferType) -> ByteListBufferType:
        packets = []
        for current_byte in packet:
            if self._in_packet:
                if self._previous_byte == self.STF:
                    byte = self.STF - current_byte
                    if byte < self.SOF:  # Invalid stuffing
                        self._in_packet = False
                    else:
                        self._packet.append(self.STF - current_byte)
                elif current_byte == self.EOF:
                    packets.append(self._packet)
                    self._in_packet = False
                elif current_byte == self.STF:
                    pass
                elif current_byte >= self.SOF:  # Invalid stuffing
                    self._in_packet = False
                else:
                    self._packet.append(current_byte)
                self._previous_byte = current_byte
            else:
                if current_byte == self.SOF:
                    self._packet = bytearray()
                    self._in_packet = True
                else:  # Out of packet data
                    self.handle_out_of_packet_data(current_byte)
                self._previous_byte = current_byte
        return packets


class PackerStream(
    AsyncChainingStream[ByteListBufferType, ByteBufferType],
    AsyncByteListIOStream,
):
    """Packer stream class is used to pack and unpack data.

    Packer stream accepts a packet as bytearray or bytes, packs it and sends it further
    to underlying stream.
    It reads bytes from it's underlying stream, adds them to containing Packer instance
    which tries to unpack a packet.
    If successfully unpacked a package is available to read.

    :param packer_class: a class to be used for packing and unpacking
    :param input_instance: input stream instance
    :param output_instance: output stream instance. If not passed, the input_instance is
                            used also as an output.
    """

    _packer: Packer

    def __init__(
        self,
        packer_class: Type[Packer],
        input_instance: Union[ByteInputStreamType, ByteIOStreamType],
        output_instance: Optional[ByteOutputStreamType] = None,
        **kwargs,
    ) -> None:
        """Initializes a _PackerStream"""
        self._packer = packer_class(**kwargs)
        super().__init__(input_instance, output_instance)

    def _read_worker(self, internal: AsyncStreamInternals[ByteListBufferType]) -> None:
        packet_data = self._read_input()
        packets = self._packer.try_unpack_data(packet_data)
        if packets:
            with internal.buffer_lock:
                internal.buffer.extend(packets)
                internal.buffer_lock.notify_all()

    def _write_worker(self, internal: AsyncStreamInternals[ByteListBufferType]) -> None:
        data_list = []
        with internal.buffer_lock:
            internal.buffer_lock.wait()
            if len(internal.buffer):
                data_list = internal.buffer[:]
                internal.buffer.clear()
        for data in data_list:
            packet = self._packer.pack_data(data)
            self._write_output(packet)


@dataclass
class _PutStreamInternal:
    buffer: bytearray = field(default_factory=bytearray)
    buffer_lock: Condition = field(default_factory=Condition)


class OutOfPacketStream(AsyncByteListInputStream):
    """Out of packet stream is used for processing data that lays outside a packet."""

    def __init__(self, packer_class: Type[Packer], **kwargs):
        """Initializes a new packer stream

        :param packer_class: Packer class to be used for packing out of packed data.
        """
        self._packer = packer_class(**kwargs)
        super().__init__()
        self._put_internal = _PutStreamInternal()

    def close(self) -> None:
        super().close()
        self._put_internal.buffer_lock.notify_all()

    def _read_worker(self, internal: ByteListInternalsType) -> None:
        data = self._get()
        packets = self._packer.try_unpack_data(data)
        if packets:
            with internal.buffer_lock:
                internal.buffer.extend(packets)
                internal.buffer_lock.notify_all()

    def _get(self) -> bytearray:
        result = bytearray()
        with self._put_internal.buffer_lock:
            if not len(self._put_internal.buffer):
                self._put_internal.buffer_lock.wait()
            result = self._put_internal.buffer
            self._put_internal.buffer = bytearray()
        return result

    def put(self, data: int) -> None:
        """Puts data byte into an incoming buffer.

        In case the stream is not opened, the data will not be written and no exception
        is thrown.

        :param data: Out of packet data to be put to incoming buffer.
        """
        if not self.is_opened:
            return
        with self._put_internal.buffer_lock:
            self._put_internal.buffer.append(data)
            self._put_internal.buffer_lock.notify_all()
