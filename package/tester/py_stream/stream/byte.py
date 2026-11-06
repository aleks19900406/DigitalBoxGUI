import re
import socket
from typing import Any, Dict, List, Optional

import serial
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo

from ._base import (
    AsyncInputStream,
    AsyncIOStream,
    AsyncOutputStream,
    AsyncStreamInternals,
    SyncIOStream,
    SyncStreamInternals,
)
from ._protocols import InputStreamType, IOStreamType, OutputStreamType

ByteBufferType = bytearray
ByteInternalsType = AsyncStreamInternals[ByteBufferType]
SyncByteInternalsType = SyncStreamInternals[ByteBufferType]

ByteInputStreamType = InputStreamType[ByteBufferType]  #: Byte Input Stream protocol
ByteOutputStreamType = OutputStreamType[ByteBufferType]  #: Byte Output Stream protocol
ByteIOStreamType = IOStreamType[ByteBufferType]  #: Byte IO Stream protocol


class AsyncByteInputStream(AsyncInputStream[ByteBufferType]):
    _BT_I = ByteBufferType
    _IT_I = ByteInternalsType


class AsyncByteOutputStream(AsyncOutputStream[ByteBufferType]):
    _BT_O = ByteBufferType
    _IT_O = ByteInternalsType


class AsyncByteIOStream(
    AsyncByteInputStream, AsyncByteOutputStream, AsyncIOStream[ByteBufferType]
):
    ...


class SyncByteIOStream(SyncIOStream[ByteBufferType]):
    _BT_I = ByteBufferType
    _BT_O = ByteBufferType
    _IT_I_O = SyncByteInternalsType


class SerialStream(AsyncByteIOStream):
    """SerialStream class

    :param port: desired port to open serial connection on, defaults to None
    :param baudrate: desired connection baud rate, defaults to 9600
    :param bytesize: size of a byte, defaults to serial.EIGHTBITS
    :param parity: parity mode, defaults to serial.PARITY_NONE
    :param stopbits: number of stop bits, defaults to serial.STOPBITS_ONE
    :param timeout: read timeout, defaults to 0.1
    :param xonxoff: flow control, defaults to False
    :param rtscts: flow control, defaults to False
    :param write_timeout: write timeout, defaults to None
    :param dsrdtr: flow control, defaults to False
    :param inter_byte_timeout: inter byte timeout, defaults to None
    :param exclusive: exclusive porto on POSIX, defaults to None
    """

    _comports: Optional[List[ListPortInfo]] = None

    def __init__(
        self,
        device_params: Dict[str, str] = None,
        baudrate: int = 9600,
        bytesize: int = serial.EIGHTBITS,
        parity: str = serial.PARITY_NONE,
        stopbits: int = serial.STOPBITS_ONE,
        timeout: float = 0.1,
        xonxoff: bool = False,
        rtscts: bool = False,
        write_timeout: Optional[float] = None,
        dsrdtr: bool = False,
        inter_byte_timeout: Optional[float] = None,
        exclusive: Optional[Any] = None,
        **kwargs,
    ) -> None:
        """Initializes a SerialStream instance"""
        if SerialStream._comports is None:
            SerialStream._comports = comports()
        super().__init__()
        self._serial = serial.Serial(
            None,
            baudrate,
            bytesize,
            parity,
            stopbits,
            timeout,
            xonxoff,
            rtscts,
            write_timeout,
            dsrdtr,
            inter_byte_timeout,
            exclusive,
            **kwargs,
        )
        device_params = device_params or {}
        port = None
        for comport in SerialStream._comports:
            args = []
            for param_name, param_regex in device_params.items():
                param = getattr(comport, param_name, "")
                args.append(bool(param) and re.fullmatch(param_regex, param))
            if all(args):
                port = comport.device
        if port is None:
            raise serial.SerialException(
                "None of connected devices match desired device parameters"
            )
        self._serial.port = port

    def __del__(self) -> None:
        self.close()

    def _open_begin(self) -> None:
        self._serial.open()

    def _close_finalize(self) -> None:
        self._serial.close()

    def flush(self) -> None:
        """Flushes outgoing data"""
        super().flush()
        self._serial.flush()

    def _read_worker(self, internal: ByteInternalsType) -> None:
        try:
            data = self._serial.read(self._serial.in_waiting or 1)
        except serial.SerialException:
            return
        if data:
            with internal.buffer_lock:
                internal.buffer.extend(data)
                internal.buffer_lock.notify_all()

    def _write_worker(self, internal: ByteInternalsType) -> None:
        data = False
        with internal.buffer_lock:
            internal.buffer_lock.wait()
            if len(internal.buffer):
                data = internal.buffer[:]
                internal.buffer.clear()
        if data:
            self._serial.write(data)


class _TCPStream(AsyncByteIOStream):
    """TCPStream base class

    :param ip: ip address of the device to connect to
    :param port: port to connect to
    :raises TypeError: in case the ip and port parameters are not present
    """

    socket = Optional[socket.socket]

    def __init__(self, ip: str = None, port: int = None) -> None:
        """Initializes a TCPStream instance"""
        if ip is None or port is None:
            raise TypeError("TCPStream missing required arguments 'ip' and 'port'")
        super().__init__()
        self._ip = ip
        self._port = port
        self._socket = None

    def _read_worker(self, internal: ByteInternalsType) -> None:
        try:
            data = self._socket.recv(1024)
        except OSError:
            return
        if data:
            with internal.buffer_lock:
                internal.buffer.extend(data)
                internal.buffer_lock.notify_all()

    def _write_worker(self, internal: ByteInternalsType) -> None:
        data = False
        with internal.buffer_lock:
            internal.buffer_lock.wait()
            if len(internal.buffer):
                data = internal.buffer[:]
                internal.buffer.clear()
        if data:
            self._socket.send(data)


class TCPStream(_TCPStream):
    """TCPStream class

    :param ip: ip address of the device to connect to
    :param port: port to connect to
    :raises TypeError: in case the ip and port parameters are not present
    """

    def _open_begin(self) -> None:
        if self._socket is None:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._ip, self._port))
        else:
            raise RuntimeError("Stream is already opened")

    def _close_begin(self) -> None:
        self._should_stop.set()
        if self._socket is not None:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()

    def _close_finalize(self) -> None:
        self._socket = None


class TCPStreamServer(_TCPStream):
    """TCPStreamServer class

    :param ip: ip address of the device to connect to
    :param port: port to connect to
    :raises TypeError: in case the ip and port parameters are not present
    """

    def __init__(self, ip: str = None, port: int = None) -> None:
        super().__init__(ip, port)
        self._server = None

    def _open_begin(self) -> None:
        if self._server is None:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server.bind((self._ip, self._port))
            self._server.listen(1)
            self._socket, _ = self._server.accept()
        else:
            raise RuntimeError("Stream is already opened")

    def _close_begin(self) -> None:
        self._should_stop.set()
        if self._socket is not None:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()
        if self._server is not None:
            self._server.close()

    def _close_finalize(self) -> None:
        self._socket = None
        self._server = None
