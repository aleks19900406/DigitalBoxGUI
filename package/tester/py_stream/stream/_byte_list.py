from typing import List

from ._base import (
    AsyncInputStream,
    AsyncIOStream,
    AsyncOutputStream,
    AsyncStreamInternals,
    SyncIOStream,
    SyncStreamInternals,
)
from ._protocols import InputStreamType, IOStreamType, OutputStreamType

ByteListBufferType = List[bytearray]
ByteListInternalsType = AsyncStreamInternals[ByteListBufferType]
SyncByteListInternalsType = SyncStreamInternals[ByteListBufferType]


ByteListInputStreamType = InputStreamType[  #: Byte List Input Stream protocol
    ByteListBufferType
]
ByteListOutputStreamType = OutputStreamType[  #: Byte List Output Stream protocol
    ByteListBufferType
]
ByteListIOStreamType = IOStreamType[ByteListBufferType]  #: Byte List IO Stream protocol


class AsyncByteListInputStream(AsyncInputStream[ByteListBufferType]):
    _BT_I = list
    _IT_I = ByteListInternalsType


class AsyncByteListOutputStream(AsyncOutputStream[ByteListBufferType]):
    _BT_O = list
    _IT_O = ByteListInternalsType


class AsyncByteListIOStream(
    AsyncByteListInputStream,
    AsyncByteListOutputStream,
    AsyncIOStream[ByteListBufferType],
):
    ...


class SyncByteListIOStream(SyncIOStream[ByteListBufferType]):
    _BT_I = list
    _BT_O = list
    _IT_I_O = SyncByteListInternalsType
