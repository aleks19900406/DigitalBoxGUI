"""Request response client"""
import json
import select
import socket
from functools import wraps
from typing import Callable, Dict, List, Optional, TypeVar, Union

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
    """TCP client to be used with tester device clients

    :param server_address: address of the server
    :param server_port: port, the server is instening on
    """

    def __init__(
        self,
        server_address: str,
        server_port: int,
    ):
        """Initializes a new request response client object"""
        self.__tcp_ip = server_address
        self.__tcp_port = server_port
        self._client = None

    @property
    def interface(self) -> Optional[str]:
        """The name of the clients network interface"""
        if self._client is not None:
            return socket.gethostbyname(self._client.getsockname()[0])
        return None

    def empty(self) -> None:
        """Empties the input queue"""
        inputs = [self._client]
        while True:
            i, _, _ = select.select(inputs, [], [], 0.0)
            if not i:
                break
            for s in i:
                s.recv(1)

    def connect(self) -> None:
        """Connects to the ResponseRequestServer

        :raises RuntimeError: in case the client is allready connected
        """
        if self._client is None:
            self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._client.connect((self.__tcp_ip, self.__tcp_port))
        else:
            raise RuntimeError("client is allready connected")

    @check_connected
    def send_request(self, data_out: Serializable) -> None:
        """Sends request to server

        :param data_out: request object
        :raises RuntimeError: in case the client is not connected
        """
        self.empty()
        self._client.send(b"".join([json.dumps(data_out).encode(), b"\x00"]))

    @check_connected
    def recv_response(self) -> Serializable:
        """Fetches response from server

        :raises RuntimeError: in case the client is not connected
        :return: response object
        """
        pkg = b" "
        try:
            while pkg[-1] is not 0:
                pkg = b"".join([pkg, self._client.recv(1)])
                if pkg == b" ":
                    break
        except socket.timeout:
            pass
        else:
            try:
                data_in = json.loads(pkg[:-1].decode())
            except json.JSONDecodeError:
                return -1, pkg
            except EOFError:
                return -2, pkg
            else:
                return data_in

    def request(self, data_out) -> Serializable:
        """Sends request and waits for response

        :raises RuntimeError: in case the client is not connected
        :return: response object
        """
        self.send_request(data_out)
        return self.recv_response()

    def disconnect(self) -> None:
        """Disconnects from the RequestResponseServer"""
        if self._client is not None:
            self._client.close()
            self._client = None
