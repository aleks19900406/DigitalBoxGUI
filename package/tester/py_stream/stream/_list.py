from typing import Generic, List, Type

from ._base import (
    AsyncInputStream,
    AsyncIOStream,
    AsyncOutputStream,
    AsyncStreamInternals,
    SyncIOStream,
    SyncStreamInternals,
)
from ._protocols import BT, InputStreamType, IOStreamType, OutputStreamType

ListInputStreamType = InputStreamType[List[BT]]  #: Byte List Input Stream protocol
ListOutputStreamType = OutputStreamType[List[BT]]  #: Byte List Output Stream protocol
ListIOStreamType = IOStreamType[List[BT]]  #: Byte List IO Stream protocol


class AsyncListInputStream(AsyncInputStream[List[BT]], Generic[BT]):
    _BT_I: Type[List[BT]] = list
    _IT_I = AsyncStreamInternals[List[BT]]


class AsyncListOutputStream(AsyncOutputStream[List[BT]], Generic[BT]):
    _BT_O: Type[List[BT]] = list
    _IT_O = AsyncStreamInternals[List[BT]]


class AsyncListIOStream(
    AsyncListInputStream,
    AsyncListOutputStream,
    AsyncIOStream[List[BT]],
):
    ...


class SyncListIOStream(SyncIOStream[List[BT]], Generic[BT]):
    _BT_I: Type[List[BT]] = list
    _BT_O: Type[List[BT]] = list
    _IT_I_O = SyncStreamInternals[List[BT]]
