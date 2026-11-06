import ctypes
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple, Union, overload

from c_tools.parser.utils import CtypesEnum, CtypesStruct

from .._base import SyncChainingStream, SyncStreamInternals
from .._byte_list import SyncByteListIOStream
from .._utils import Timer
from ..byte import ByteBufferType, ByteIOStreamType
from ..coder import CheckSumCoder, Coder, CoderDecodeError, CRCCoder
from ..packer import HisensePacker


# region Helpers
class Structure(CtypesStruct):
    """Use for single byte length only"""

    _packed_ = True

    def __int__(self) -> int:
        return int.from_bytes(self, "little", signed=False)

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            + ", ".join([f"{i[0]}={getattr(self, i[0])}" for i in self._fields_])
            + ")"
        )

    def __iter__(self) -> Iterator[int]:
        yield from bytes(self)


class FrameBase(ABC):
    """Hisense layer frame base"""

    def __bytes__(self) -> bytes:
        return bytes(self.__iter__())

    @abstractmethod
    def __iter__(self) -> Iterator[int]:
        ...


# endregion Helpers

# region Link Layer
class LLResponseId(CtypesEnum):
    """Link Layer response ids"""

    TRSM = 0x00  # Master transmit
    FAIL = 0x00  # Network layer error
    SUCCESS = 0x01  # Success
    ERROR = 0x08  # LL Id2 is present or checksum method is not supported


class ChecksumType(CtypesEnum):
    """Available checksum coders"""

    CHECKSUM8 = 0
    CHECKSUM16 = 1
    CRC16 = 2
    CRC32 = 3


class NotImplementedCoder(Coder):
    """Dummy coder"""

    def encode(self, data: bytearray) -> bytearray:
        raise NotImplementedError("coder is not implemented")

    def decode(self, data: bytearray) -> bytearray:
        raise NotImplementedError("coder is not implemented")


CHECKSUM_CODER: Dict[int, Coder] = {
    ChecksumType.CHECKSUM8: CheckSumCoder(),
    ChecksumType.CHECKSUM16: CheckSumCoder(2, "big"),  # TODO: Hard coded - FOR WM?
    ChecksumType.CRC16: CRCCoder("lte16"),
    ChecksumType.CRC32: NotImplementedCoder(),
}

CHECKSUM_LENGTH: Dict[int, int] = {
    ChecksumType.CHECKSUM8: 1,
    ChecksumType.CHECKSUM16: 2,
    ChecksumType.CRC16: 2,
    ChecksumType.CRC32: 4,
}


class LLId1(Structure):
    """Link Layer id1"""

    ll2_present: int
    frame_number: int
    nl_len_repr_size: int  #: 0: 1 byte, 1: 2 bytes
    checksum_type: int
    _fields_ = [
        ("ll2_present", ctypes.c_uint8, 1),
        ("frame_number", ctypes.c_uint8, 4),
        ("nl_len_repr_size", ctypes.c_uint8, 1),
        ("checksum_type", ctypes.c_uint8, 2),
    ]


@dataclass
class _LLFrame(FrameBase):
    response_id: LLResponseId = LLResponseId.TRSM
    id1: LLId1 = LLId1()
    id2: Optional[int] = None
    id3: Optional[int] = None
    nl_length: int = 0
    payload: bytearray = field(default_factory=bytearray)


class LLFrame(_LLFrame):
    """Link Layer frame"""

    @overload
    def __init__(
        self,
        response_id: LLResponseId,
        id1: LLId1,
        id2: Optional[int],
        id3: Optional[int],
        nl_length: int,
        payload: bytearray,
    ) -> None:
        ...

    @overload
    def __init__(self, buffer: bytearray) -> None:
        ...

    def __init__(self, *args, **kwargs) -> None:
        from_buffer = len(args) == 1 and isinstance(args[0], (bytes, bytearray))
        if from_buffer:
            try:
                kwargs = {}
                it = iter(args[0])
                args = ()
                kwargs["response_id"] = LLResponseId(next(it))
                id1 = LLId1.from_buffer_copy(bytearray([next(it)]))
                kwargs["id1"] = id1
                if id1.ll2_present:
                    kwargs["id2"] = next(it)
                nl_length = (
                    (next(it) << 8) + next(it) if id1.nl_len_repr_size else next(it)
                )
                kwargs["nl_length"] = nl_length
                kwargs["payload"] = bytearray(next(it) for _ in range(nl_length))
            except Exception as ex:
                raise ValueError("invalid buffer length") from None
        else:
            if len(args[-1]) != args[-2]:
                raise ValueError("invalid buffer length")
        super().__init__(*args, **kwargs)
        if not from_buffer and self.nl_length == 0:
            self.nl_length = len(self.payload)

    def __iter__(self) -> Iterator[int]:
        yield self.response_id.value
        yield from self.id1
        if self.id1.ll2_present:
            if self.id2 is None:
                raise ValueError("invalid id2 representation")
            yield self.id2
        try:
            yield from self.nl_length.to_bytes(
                2 if self.id1.nl_len_repr_size else 1, "big", signed=False
            )
        except OverflowError:
            raise ValueError("invalid NL length representation")
        yield from self.payload


# endregion Link Layer

# region Network Layer
class HisenseNLException(Exception):
    """Hisense Network Layer Exception object"""


class DeviceFamily(CtypesEnum):
    """Supported device families"""

    UNKNOWN = 0x00
    FRIDGE = 0x02
    DISH_WASHER = 0x07
    DRYER = 0x08
    WASHING_MACHINE = 0x09
    OVEN = 0x27
    WIFI = 0xFE
    BROADCAST = 0xFF


NLResponseId = LLResponseId


class NLId1(Structure):
    """Network Layer id1"""

    nl2_present: int  #: whether the second identification is present or not
    addr_len_repr_size: int  #: device address code length
    all_addresses_present: int  #: indicates whether addresses are present
    addressing: int  #: use DeviceFamily addressing
    _packed_ = True
    _fields_ = [
        ("nl2_present", ctypes.c_uint8, 1),
        ("RESERVED", ctypes.c_uint8, 2),
        ("addr_len_repr_size", ctypes.c_uint8, 2),
        ("all_addresses_present", ctypes.c_uint8, 1),
        ("addressing", ctypes.c_uint8, 2),
    ]


class NLAddress(ctypes.Structure):
    """Network Layer address"""

    device_family: int
    device_number: int

    _packed_ = True
    _fields_ = [("device_family", DeviceFamily), ("device_number", ctypes.c_uint8)]

    def __iter__(self) -> Iterator[int]:
        yield self.device_family
        yield self.device_number


@dataclass
class _NLFrame:
    response_id: NLResponseId = NLResponseId.TRSM
    id1: NLId1 = field(default_factory=NLId1)
    id2: Optional[int] = None
    id3: Optional[int] = None
    addr1: NLAddress = field(default_factory=NLAddress)
    addr2: NLAddress = field(default_factory=NLAddress)
    addr3: Optional[NLAddress] = None
    addr4: Optional[NLAddress] = None
    addr5: Optional[NLAddress] = None
    payload: bytearray = field(default_factory=bytearray)


class NLFrame(_NLFrame):
    """Network Layer frame"""

    @overload
    def __init__(
        self,
        response_id: NLResponseId,
        id1: NLId1,
        id2: Optional[int],
        id3: Optional[int],
        addr1: NLAddress,
        addr2: NLAddress,
        addr3: Optional[NLAddress],
        addr4: Optional[NLAddress],
        addr5: Optional[NLAddress],
        payload: bytearray,
    ) -> None:
        ...

    @overload
    def __init__(self, buffer: Union[bytes, bytearray]) -> None:
        ...

    def __init__(self, *args, **kwargs) -> None:
        if len(args) == 1 and isinstance(args[0], (bytes, bytearray)):
            try:
                kwargs = {}
                it = iter(args[0])
                args = ()
                kwargs["response_id"] = NLResponseId(next(it))
                id1 = NLId1(next(it))
                kwargs["id1"] = id1
                if id1.nl2_present:
                    kwargs["id2"] = next(it)
                kwargs["addr1"] = NLAddress(next(it), next(it))
                kwargs["addr2"] = NLAddress(next(it), next(it))
                if id1.all_addresses_present:
                    kwargs["addr3"] = NLAddress(next(it), next(it))
                    kwargs["addr4"] = NLAddress(next(it), next(it))
                    kwargs["addr5"] = NLAddress(next(it), next(it))
                kwargs["payload"] = bytearray(it)
            except StopIteration:
                raise ValueError("invalid buffer length")
        super().__init__(*args, **kwargs)

    def __bytes__(self) -> bytes:
        return bytes(self.__iter__())

    def __iter__(self) -> Iterator[int]:
        yield self.response_id.value
        yield int(self.id1)
        if self.id1.nl2_present:
            if self.id2 is None:
                raise ValueError("invalid id2 representation")
            yield self.id2
        yield from self.addr1
        yield from self.addr2
        if self.id1.all_addresses_present:
            if self.addr3 is None:
                raise ValueError("invalid addr3 representation")
            yield from self.addr3
            if self.addr4 is None:
                raise ValueError("invalid addr4 representation")
            yield from self.addr4
            if self.addr5 is None:
                raise ValueError("invalid addr5 representation")
            yield from self.addr5
        yield from self.payload


# endregion Network Layer

# region Transport Layer
class HisenseTLException(Exception):
    """Hisense Transport Layer Exception"""


class TLEncryption(CtypesEnum):
    NO_ENCRYPTION = 0x00  # Transmission layer does not use encryption


class TLStatus(CtypesEnum):
    MASTER = 0x00
    FAIL = 0x00
    SUCCESS = 0x01
    ERROR = 0x08


class TLResponseId(Structure):
    status: int
    encryption: int
    _fields_ = [
        ("status", TLStatus, 4),
        ("encryption", TLEncryption, 4),
    ]


class TLId1(Structure):
    tl2_present: int
    al_encripted: int
    _fields_ = [
        ("tl2_present", ctypes.c_uint8, 1),
        ("RESERVED", ctypes.c_uint8, 3),
        ("al_encripted", ctypes.c_uint8, 4),
    ]


@dataclass
class _TLFrame:
    response_id: TLResponseId = TLResponseId()
    id1: TLId1 = TLId1()
    id2: Optional[int] = None
    id3: Optional[int] = None
    payload: bytearray = field(default_factory=bytearray)


class TLFrame(_TLFrame):
    @overload
    def __init__(
        self,
        response_id: TLResponseId,
        id1: TLId1,
        id2: Optional[int],
        id3: Optional[int],
        payload: bytearray,
    ) -> None:
        ...

    @overload
    def __init__(self, buffer: Union[bytes, bytearray]) -> None:
        ...

    def __init__(self, *args, **kwargs) -> None:
        if len(args) == 1 and isinstance(args[0], (bytes, bytearray)):
            try:
                kwargs = {}
                buffer = args[0]
                it = iter(buffer)
                kwargs["response_id"] = TLResponseId.from_buffer_copy(
                    bytearray([next(it)])
                )
                id1 = TLId1.from_buffer_copy(bytearray([next(it)]))
                kwargs["id1"] = id1
                if id1.tl2_present:
                    kwargs["id2"] = next(it)
                if id1.al_encripted:
                    # TODO: Encryption not supported
                    raise HisenseTLException("Encryption not supported")
                kwargs["payload"] = bytearray(it)
            except StopIteration:
                raise ValueError("invalid buffer length")
            super().__init__(**kwargs)
        else:
            super().__init__(*args, **kwargs)

    def __bytes__(self) -> bytes:
        return bytes(self.__iter__())

    def __iter__(self) -> Iterator[int]:
        yield int(self.response_id)
        yield int(self.id1)
        if self.id1.tl2_present:
            if self.id2 is None:
                raise ValueError("invalid id2 representation")
            yield self.id2
        if self.id1.al_encripted:
            raise HisenseTLException("Encryption not supported")
        yield from self.payload


# endregion Transport Layer

# region Application Layer
@dataclass
class _ALFrame:
    command: bytearray = field(default_factory=bytearray)
    payload: bytearray = field(default_factory=bytearray)


class ALFrame(_ALFrame):
    @overload
    def __init__(
        self,
        command: bytes,
        payload: bytearray,
    ) -> None:
        ...

    @overload
    def __init__(self, buffer: Union[bytes, bytearray]) -> None:
        ...

    def __init__(self, *args, **kwargs) -> None:
        if len(args) == 1:
            kwargs = {}
            buffer = args[0]
            kwargs["command"] = buffer[:2]
            kwargs["payload"] = buffer[2:]
            super().__init__(**kwargs)
        else:
            super().__init__(*args, **kwargs)

    def __bytes__(self) -> bytes:
        return bytes(self.__iter__())

    def __iter__(self) -> Iterator[int]:
        yield from self.command
        yield from self.payload


ALStreamBufferItemType = Tuple[int, bytes, ByteBufferType]
ALStreamBufferType = List[ALStreamBufferItemType]

# endregion Application Layer

_InternalType = SyncStreamInternals[ALStreamBufferType]


class HisenseStrem(
    SyncChainingStream[ALStreamBufferType, bytearray], SyncByteListIOStream
):

    TIMEOUT = 2  # 2s timeout as described in specification
    N_TRIES = 10  # initial request + 9 retries as described in specification

    _BT_I = list
    _BT_O = list
    _IT_I_O = _InternalType

    def __init__(
        self,
        underlying_stream: ByteIOStreamType,
        device_family: int,
        checksum_type: int = ChecksumType.CRC16,
    ) -> None:
        self._packer = HisensePacker()
        super().__init__(underlying_stream, underlying_stream)
        self._device_family = device_family
        self._checksum_type = checksum_type
        self._frame_no = 0

    def get_frame_no(self) -> int:
        self._frame_no = (self._frame_no + 1) % 16
        return self._frame_no

    def peek_frame_no(self) -> int:
        return self._frame_no

    def _r_w_worker(self, internal: _InternalType) -> None:
        """Thread entry"""
        data = self._get_write_data(internal)
        if data is not None:
            data_in = self._write_request_and_read_response(data)
            self._set_read_data(internal, data_in)

    def _get_write_data(
        self, internal: _InternalType
    ) -> Optional[ALStreamBufferItemType]:
        with internal.buffer_lock:
            if not internal.write_buffer:
                internal.buffer_lock.wait()
            if internal.write_buffer:
                return internal.write_buffer.pop()
        return None

    def _set_read_data(
        self, internal: _InternalType, data: ALStreamBufferItemType
    ) -> None:
        with internal.buffer_lock:
            internal.read_buffer.append(data)
            internal.buffer_lock.notify_all()

    def _write_request_and_read_response(
        self, data: ALStreamBufferItemType
    ) -> ALStreamBufferItemType:
        for _ in range(self.N_TRIES):
            self._write_request(data)
            data_in = self._read_response()
            if data_in is not None:
                return data_in
        raise RuntimeError("retry limit reached")

    def _write_request(self, data: ALStreamBufferItemType) -> None:
        ll_frame = self._wrap_data(*data)
        coded = CHECKSUM_CODER[self._checksum_type].encode(bytearray(ll_frame))
        packed = self._packer.pack_data(coded)
        self._output.write(packed)

    def _read_response(self) -> Optional[ALStreamBufferItemType]:
        with Timer(self.TIMEOUT) as timer:
            while not timer.expired:
                raw_data = self._input.read(
                    self._input.in_waiting or 1, timeout=timer.remaining
                )
                if not raw_data:
                    continue
                packets = self._packer.try_unpack_data(raw_data)
                for packet in packets:
                    try:
                        ll_frame = LLFrame(packet)
                        if len(bytes(ll_frame)) + CHECKSUM_LENGTH[
                            ChecksumType(ll_frame.id1.checksum_type)
                        ] != len(packet):
                            raise ValueError()
                    except ValueError:
                        raise NotImplementedError(
                            "received message is of invalid length"
                        ) from None
                    try:
                        CHECKSUM_CODER[ChecksumType(ll_frame.id1.checksum_type)].decode(
                            packet
                        )
                    except CoderDecodeError:
                        raise NotImplementedError("checksum does not match") from None
                    pealed = self._peel_data(ll_frame)
                    if pealed is not None:  # message was for me
                        return pealed

    # region Pealers
    def _peel_data(self, frame: LLFrame) -> Optional[Tuple[int, bytes, bytearray]]:
        nl_frame = self._peel_link_layer(frame)
        if nl_frame is None:
            return None
        unpeeled_nl = self._peel_network_layer(nl_frame)
        if unpeeled_nl is None:
            return None
        al_frame = self._peel_transport_layer(unpeeled_nl[1])
        return unpeeled_nl[0], al_frame.command, al_frame.payload

    def _peel_link_layer(self, frame: LLFrame) -> Optional[NLFrame]:
        if frame.response_id == LLResponseId.SUCCESS:
            if frame.id1.ll2_present:
                raise NotImplementedError("second LL Id is not supported")
            elif frame.id1.frame_number != self.peek_frame_no():
                return None  # Invalid frame number. Possibly frame is not for me.
            return NLFrame(frame.payload)
        elif frame.response_id == LLResponseId.FAIL:
            raise NotImplementedError(
                "transmission failed; link layer fail not implemented"
            )
        elif frame.response_id == LLResponseId.ERROR:
            raise TypeError(f"unsupported checksum type {frame.id1.checksum_type}")
        else:
            raise RuntimeError("unknown error on link layer")

    def _peel_network_layer(self, frame: NLFrame) -> Optional[Tuple[int, TLFrame]]:
        if frame.response_id == NLResponseId.SUCCESS:
            if frame.addr2.device_family == self._device_family:
                return frame.addr2.device_number, TLFrame(frame.payload)
            else:
                return None  # TODO: Package not for me. Is it OK to pass?
        elif frame.response_id == NLResponseId.FAIL:
            raise RuntimeError("network layer should never have failed")
        elif frame.response_id == NLResponseId.ERROR:
            raise NotImplementedError("network layer error occurred")
        else:
            raise RuntimeError("unknown error on network layer")

    def _peel_transport_layer(self, frame: TLFrame) -> ALFrame:
        if frame.response_id.status == TLStatus.SUCCESS:
            if frame.response_id.encryption == TLEncryption.NO_ENCRYPTION:
                if not frame.id1.al_encripted:
                    return ALFrame(frame.payload)
                else:
                    raise NotImplementedError("AL encryption not supported yet")
            else:
                raise NotImplementedError("TL encryption not supported yet")
        elif frame.response_id.status == TLResponseId.FAIL:
            raise RuntimeError("transport layer should never have failed")
        elif frame.response_id.status == TLResponseId.ERROR:
            raise NotImplementedError("transport layer error occurred")
        else:
            raise RuntimeError("unknown error on transport layer")

    # endregion Pealers

    # region Wrappers
    def _wrap_data(
        self, device_number: int, command: bytes, payload: bytearray
    ) -> LLFrame:
        tl_frame = self._wrap_transport_layer(ALFrame(command, payload))
        nl_frame = self._wrap_network_layer(device_number, tl_frame)
        return self._wrap_link_layer(nl_frame)

    def _wrap_transport_layer(self, frame: ALFrame) -> TLFrame:
        return TLFrame(
            TLResponseId(TLStatus.MASTER, TLEncryption.NO_ENCRYPTION),
            TLId1(0, 0, 0),
            0,
            0,
            bytearray(frame),
        )

    def _wrap_network_layer(self, device_number: int, frame: TLFrame) -> NLFrame:
        return NLFrame(
            NLResponseId.TRSM,
            NLId1(),
            None,
            None,
            NLAddress(self._device_family, device_number),
            NLAddress(DeviceFamily.WIFI, 0x01),
            None,
            None,
            None,
            bytearray(frame),
        )

    def _wrap_link_layer(self, frame: NLFrame) -> LLFrame:
        payload = bytearray(frame)
        return LLFrame(
            LLResponseId.TRSM,
            LLId1(0, self.get_frame_no(), len(payload) > 255, self._checksum_type),
            None,
            None,
            len(payload),
            payload,
        )

    # endregion Wrappers
