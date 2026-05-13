"""Request response client"""
import json
import select
import socket
from functools import wraps
from typing import Callable, Dict, List, Optional, TypeVar, Union
from time import sleep
import threading
FT = TypeVar("FT")


def check_connected(f: FT) -> FT:
    """Decorator to check if object is connected"""

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self._client is None:  # pylint: disable=protected-access
            raise RuntimeError(f"{self.__class__.__name__} is not connected")
        return f(self, *args, **kwargs)

    return wrapper


Serializable = Union[None, int, float, str, List, Dict]


class RequestResponseClient:
    """TCP client to be used with tester device clients.

    Robustna verzija za delo prek VPN / nestabilnega TCP.
    Uporablja:
    - connect timeout
    - I/O timeout
    - sendall
    - internal RX buffer
    - bounded stale-data draining
    - optional auto-reconnect once on broken request
    """

    CONNECT_TIMEOUT = 8.0
    IO_TIMEOUT = 20.0
    RETRY_SLEEP = 1.0
    MAX_DRAIN_BYTES = 4096
    MAX_MESSAGE_SIZE = 4 * 1024 * 1024  # 4 MB

        
    def __init__(
        self,
        server_address: str,
        server_port: int,
        connect_timeout: float = CONNECT_TIMEOUT,
        io_timeout: float = IO_TIMEOUT,
        auto_reconnect_once: bool = True,
    ):
        self.__tcp_ip = server_address
        self.__tcp_port = server_port
        self._client = None
        self._connect_timeout = connect_timeout
        self._io_timeout = io_timeout
        self._auto_reconnect_once = auto_reconnect_once
        self._rx_buffer = bytearray()
        self._lock = threading.RLock()


    @property
    def interface(self) -> Optional[str]:
        """The name/IP of the client's local network interface."""
        if self._client is not None:
            return socket.gethostbyname(self._client.getsockname()[0])
        return None

    def _create_socket(self) -> socket.socket:
        """Create and connect a socket with timeouts."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self._connect_timeout)
        sock.connect((self.__tcp_ip, self.__tcp_port))
        sock.settimeout(self._io_timeout)
        return sock

    def _reconnect(self, reason: str = "") -> None:
        """Reconnect underlying socket."""
        if reason:
            print(f"RequestResponseClient reconnect: {reason}")

        self.disconnect()
        sleep(self.RETRY_SLEEP)
        self.connect()

    def empty(self) -> None:
        """Empties stale input data from the socket and internal buffer.

        Če je v socketu preveč "smeti", se povezava smatra kot razsynchronizirana
        in se reconnecta.
        """
        if self._client is None:
            return

        # Počisti interni buffer
        self._rx_buffer.clear()

        drained = 0
        try:
            while True:
                readable, _, _ = select.select([self._client], [], [], 0.0)
                if not readable:
                    return

                chunk = self._client.recv(min(1024, self.MAX_DRAIN_BYTES - drained))
                if chunk == b"":
                    raise ConnectionResetError("Peer closed connection while draining input")

                drained += len(chunk)

                if drained >= self.MAX_DRAIN_BYTES:
                    self._reconnect("too much stale buffered data")
                    return

        except (socket.timeout, OSError, ConnectionError) as e:
            self._reconnect(f"drain failed: {e}")
    
    def connect(self) -> None:
        """Connects to the RequestResponseServer."""
        with self._lock:
            if self._client is not None:
                raise RuntimeError("client is already connected")

            try:
                self._client = self._create_socket()
                self._rx_buffer.clear()
            except (socket.timeout, OSError) as e:
                self._client = None
                raise RuntimeError(
                    f"Failed to connect to {self.__tcp_ip}:{self.__tcp_port}: {e}"
                ) from e

    @check_connected
    def send_request(self, data_out) -> None:
        """Sends request to server.

        :param data_out: request object
        """
        payload = json.dumps(data_out).encode("utf-8") + b"\x00"

        try:
            # Pred vsakim requestom odstrani morebitne stale bajte
            self.empty()
            self._client.sendall(payload)
        except (socket.timeout, BrokenPipeError, ConnectionResetError, OSError) as e:
            raise RuntimeError(f"Failed to send request: {e}") from e

    @check_connected
    def recv_response(self):
        """Fetches response from server.

        Protokol predvideva JSON + null terminator (\\x00).
        Uporablja interni buffer, da ohrani morebitne presežne bajte.

        :raises RuntimeError: v primeru timeouta, prekinjene povezave ali neveljavnega JSON
        :return: deserializiran JSON objekt
        """
        try:
            while True:
                # Če je terminator že v bufferju, obdelaj takoj
                terminator_index = self._rx_buffer.find(0)
                if terminator_index != -1:
                    raw_msg = bytes(self._rx_buffer[:terminator_index])
                    del self._rx_buffer[: terminator_index + 1]

                    if not raw_msg:
                        raise RuntimeError("Received empty response payload")

                    try:
                        return json.loads(raw_msg.decode("utf-8"))
                    except json.JSONDecodeError as e:
                        raise RuntimeError(
                            f"Invalid JSON response from server: {raw_msg!r}"
                        ) from e
                    except UnicodeDecodeError as e:
                        raise RuntimeError(
                            f"Invalid UTF-8 response from server: {raw_msg!r}"
                        ) from e

                # Preveč podatkov brez terminatorja -> nekaj je narobe
                if len(self._rx_buffer) > self.MAX_MESSAGE_SIZE:
                    raise RuntimeError("Response exceeds maximum allowed size")

                chunk = self._client.recv(4096)
                if chunk == b"":
                    raise ConnectionResetError("Peer closed connection while waiting for response")

                self._rx_buffer.extend(chunk)

        except socket.timeout as e:
            raise TimeoutError(
                f"Timed out while waiting for response from "
                f"{self.__tcp_ip}:{self.__tcp_port}"
            ) from e
        except (OSError, ConnectionError) as e:
            raise RuntimeError(f"Failed to receive response: {e}") from e

    def request(self, data_out):
        
        """Send request and wait for response.

            Transport layer does not perform service recovery by itself.
            Recovery is handled in RawClient.
        """
        with self._lock:
            self.send_request(data_out)
            return self.recv_response()


   
    def disconnect(self) -> None:
        """Disconnects from the RequestResponseServer."""
        with self._lock:
            if self._client is not None:
                try:
                    try:
                        self._client.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    self._client.close()
                finally:
                    self._client = None
                    self._rx_buffer.clear()

