""".. note::

    This is a very clumsy implementation of Inspector protocol.
    Only for communication with dw5060
"""
from ctypes import ArgumentError
from time import time
from typing import Iterator, List, Optional, Sequence, Union, cast, overload

from .._base import SyncChainingStream, SyncStreamInternals
from ..byte import ByteIOStreamType
from ..coder import Coder, CoderDecodeError
from ..packer import InspectorPacker, PackerStream
from .hisense import FrameBase


class InspectorCoder(Coder):
    LOOKUP = [
        0x0000,
        0x1021,
        0x2042,
        0x3063,
        0x4084,
        0x50A5,
        0x60C6,
        0x70E7,
        0x8108,
        0x9129,
        0xA14A,
        0xB16B,
        0xC18C,
        0xD1AD,
        0xE1CE,
        0xF1EF,
        0x1231,
        0x0210,
        0x3273,
        0x2252,
        0x52B5,
        0x4294,
        0x72F7,
        0x62D6,
        0x9339,
        0x8318,
        0xB37B,
        0xA35A,
        0xD3BD,
        0xC39C,
        0xF3FF,
        0xE3DE,
        0x2462,
        0x3443,
        0x0420,
        0x1401,
        0x64E6,
        0x74C7,
        0x44A4,
        0x5485,
        0xA56A,
        0xB54B,
        0x8528,
        0x9509,
        0xE5EE,
        0xF5CF,
        0xC5AC,
        0xD58D,
        0x3653,
        0x2672,
        0x1611,
        0x0630,
        0x76D7,
        0x66F6,
        0x5695,
        0x46B4,
        0xB75B,
        0xA77A,
        0x9719,
        0x8738,
        0xF7DF,
        0xE7FE,
        0xD79D,
        0xC7BC,
        0x48C4,
        0x58E5,
        0x6886,
        0x78A7,
        0x0840,
        0x1861,
        0x2802,
        0x3823,
        0xC9CC,
        0xD9ED,
        0xE98E,
        0xF9AF,
        0x8948,
        0x9969,
        0xA90A,
        0xB92B,
        0x5AF5,
        0x4AD4,
        0x7AB7,
        0x6A96,
        0x1A71,
        0x0A50,
        0x3A33,
        0x2A12,
        0xDBFD,
        0xCBDC,
        0xFBBF,
        0xEB9E,
        0x9B79,
        0x8B58,
        0xBB3B,
        0xAB1A,
        0x6CA6,
        0x7C87,
        0x4CE4,
        0x5CC5,
        0x2C22,
        0x3C03,
        0x0C60,
        0x1C41,
        0xEDAE,
        0xFD8F,
        0xCDEC,
        0xDDCD,
        0xAD2A,
        0xBD0B,
        0x8D68,
        0x9D49,
        0x7E97,
        0x6EB6,
        0x5ED5,
        0x4EF4,
        0x3E13,
        0x2E32,
        0x1E51,
        0x0E70,
        0xFF9F,
        0xEFBE,
        0xDFDD,
        0xCFFC,
        0xBF1B,
        0xAF3A,
        0x9F59,
        0x8F78,
        0x9188,
        0x81A9,
        0xB1CA,
        0xA1EB,
        0xD10C,
        0xC12D,
        0xF14E,
        0xE16F,
        0x1080,
        0x00A1,
        0x30C2,
        0x20E3,
        0x5004,
        0x4025,
        0x7046,
        0x6067,
        0x83B9,
        0x9398,
        0xA3FB,
        0xB3DA,
        0xC33D,
        0xD31C,
        0xE37F,
        0xF35E,
        0x02B1,
        0x1290,
        0x22F3,
        0x32D2,
        0x4235,
        0x5214,
        0x6277,
        0x7256,
        0xB5EA,
        0xA5CB,
        0x95A8,
        0x8589,
        0xF56E,
        0xE54F,
        0xD52C,
        0xC50D,
        0x34E2,
        0x24C3,
        0x14A0,
        0x0481,
        0x7466,
        0x6447,
        0x5424,
        0x4405,
        0xA7DB,
        0xB7FA,
        0x8799,
        0x97B8,
        0xE75F,
        0xF77E,
        0xC71D,
        0xD73C,
        0x26D3,
        0x36F2,
        0x0691,
        0x16B0,
        0x6657,
        0x7676,
        0x4615,
        0x5634,
        0xD94C,
        0xC96D,
        0xF90E,
        0xE92F,
        0x99C8,
        0x89E9,
        0xB98A,
        0xA9AB,
        0x5844,
        0x4865,
        0x7806,
        0x6827,
        0x18C0,
        0x08E1,
        0x3882,
        0x28A3,
        0xCB7D,
        0xDB5C,
        0xEB3F,
        0xFB1E,
        0x8BF9,
        0x9BD8,
        0xABBB,
        0xBB9A,
        0x4A75,
        0x5A54,
        0x6A37,
        0x7A16,
        0x0AF1,
        0x1AD0,
        0x2AB3,
        0x3A92,
        0xFD2E,
        0xED0F,
        0xDD6C,
        0xCD4D,
        0xBDAA,
        0xAD8B,
        0x9DE8,
        0x8DC9,
        0x7C26,
        0x6C07,
        0x5C64,
        0x4C45,
        0x3CA2,
        0x2C83,
        0x1CE0,
        0x0CC1,
        0xEF1F,
        0xFF3E,
        0xCF5D,
        0xDF7C,
        0xAF9B,
        0xBFBA,
        0x8FD9,
        0x9FF8,
        0x6E17,
        0x7E36,
        0x4E55,
        0x5E74,
        0x2E93,
        0x3EB2,
        0x0ED1,
        0x1EF0,
    ]

    _endianness = "big"

    def encode(self, data: Sequence[int]) -> bytearray:
        return bytearray([*data, *self._crc(data).to_bytes(2, self._endianness)])

    def decode(self, data: Sequence[int]) -> bytearray:
        crc = int.from_bytes(data[-2:], self._endianness)
        data = bytearray(data[:-2])
        if crc != self._crc(data):
            raise CoderDecodeError("data crc does not match")
        return data

    @classmethod
    def _crc(cls, data: Sequence[int], init=None) -> int:
        crc_val = init or 0x1D0F
        for byte in data:
            lookup_index = (byte ^ (crc_val >> 8)) & 0xFF
            crc_val = (cls.LOOKUP[lookup_index] ^ (crc_val << 8)) & 0xFFFFFFFF
        return crc_val & 0xFFFF


class FrameType:
    EMP = 0x00
    HLO = 0x01
    DAT = 0x02
    ERR = 0x03
    ACK = 0xFB
    NAK = 0xFC


class InspectorFrame(FrameBase):
    @overload
    def __init__(self, buffer: Union[bytes, bytearray]) -> None:
        ...

    @overload
    def __init__(
        self,
        type: Optional[int],
        number: Optional[int],
        payload: Union[bytes, bytearray],
    ) -> None:
        ...

    @overload
    def __init__(self) -> None:
        ...

    def __init__(self, *args) -> None:
        if len(args) == 0:
            type = None
            number = None
            payload = bytearray()
        elif len(args) == 1:
            try:
                it = iter(args[0])
                type = next(it)
                number = next(it)
                payload = bytearray(i for i in it)
            except StopIteration:
                raise ValueError("provided buffer is too short") from None
        elif len(args) == 3:
            type = args[0]
            number = args[1]
            payload = args[2]
        else:
            raise ArgumentError("invalid construction arguments")
        self.type = type
        self.number = number
        self.payload = payload
        self.timeout: float = 0

    def __iter__(self) -> Iterator[int]:
        if self.type is None or self.number is None:
            raise TypeError("inspector frame is not complete")
        yield self.type
        yield self.number
        yield from self.payload

    def __str__(self) -> str:
        return f"Frame(type={self.type}, number={self.number}, payload={self.payload})"


class InspectorStream(SyncChainingStream[List[bytearray], List[bytearray]]):
    _BT_I = list
    _BT_O = list
    _IT_I_O = SyncStreamInternals[List[bytearray]]

    def __init__(
        self,
        underlying_stream: ByteIOStreamType,
    ) -> None:

        packer = PackerStream(InspectorPacker, underlying_stream)
        self._coder = InspectorCoder()
        self._frame_number = 0
        self._current_out: Optional[InspectorFrame] = None
        self._last_receive: float = 0
        self._hlo_pending: float = 0
        super().__init__(packer, output_instance=packer)

    def open(self) -> None:
        self._hlo_pending = 0
        self._last_receive = 0
        self._current_out = None
        return super().open()

    def _get_number(self):
        fr_num = self._frame_number
        self._frame_number = (self._frame_number + 1) % InspectorPacker.SOF
        return fr_num

    def _feedback(self, type: int, number: int):
        ack_frame = InspectorFrame(type, self._get_number(), bytearray([number]))
        self._send_frame(ack_frame)

    def _send_frame(self, frame: InspectorFrame) -> None:
        self._output.write([self._coder.encode(bytearray(frame))])

    def _process_frame(self, data: bytearray) -> Optional[InspectorFrame]:
        try:
            data = self._coder.decode(data)
        except CoderDecodeError:
            self._feedback(FrameType.NAK, data[1])
        frame = InspectorFrame(data)
        if frame.type is FrameType.DAT:
            self._feedback(FrameType.ACK, cast(int, frame.number))
            return frame
        elif frame.type is FrameType.ACK:
            self._hlo_pending = 0
            self._current_out = None
        elif frame.type is FrameType.NAK:
            raise NotImplementedError("NAK return type not supported")

    def _r_w_worker(self, internal: SyncStreamInternals[List[bytearray]]) -> None:
        if (time() - self._last_receive) >= 25:
            if self._hlo_pending == 0:
                frame = InspectorFrame(
                    FrameType.HLO, self._get_number(), bytearray([2])
                )
                self._send_frame(frame)
                self._hlo_pending = time()
            elif (time() - self._hlo_pending) >= 25:
                raise RuntimeError("Hello message timed out")
        elif self._current_out is None:
            payload = None
            with internal.buffer_lock:
                if not internal.write_buffer:
                    internal.buffer_lock.wait(0.01)
                if internal.write_buffer:
                    payload = internal.write_buffer.pop()
            if payload:
                self._current_out = InspectorFrame(
                    FrameType.DAT, self._get_number(), payload
                )
        else:
            if self._current_out.timeout == 0:
                self._current_out.timeout = time() + 1
                self._send_frame(self._current_out)
            elif self._current_out.timeout <= time():
                raise NotImplementedError(f"frame {self._current_out.number} timed out")
        packets = self._input.read(timeout=0.01)
        if packets:
            self._last_receive = time()
            for packet in packets:
                if (frame := self._process_frame(packet)) is not None:
                    with internal.buffer_lock:
                        internal.read_buffer.append(frame.payload)
                        internal.buffer_lock.notify_all()
