"""Client templates – VPN & XML-RPC safe version"""

import socket
import time 
from time import sleep
from enum import Enum
from typing import Any, Dict, List, Union
from xmlrpc.client import ServerProxy, Transport

from .request_response_client import RequestResponseClient, Serializable

SERVER_ERROR_STR = "something went wrong on service side - contact support!"

ATTR_GROUP = "group"
ATTR_SUBGROUP = "subgroup"
ATTR_MODE = "mode"
ATTR_VALUE = "value"

MODE_SET = "set"
MODE_GET = "get"

IPV4_ALL = "0.0.0.0"
IPV4_LOCAL = "127.0.0.1"


# ===============================
# XML-RPC TRANSPORT WITH TIMEOUT
# ===============================

class TimeoutTransport(Transport):
    def __init__(self, timeout: int = 5):
        super().__init__()
        self.timeout = timeout

    def make_connection(self, host):
        conn = super().make_connection(host)
        conn.timeout = self.timeout
        return conn


# ===============================
# SERVICE STATE ENUM
# ===============================

class ServiceState(Enum):
    STOPPED = 0
    STARTING = 10
    RUNNING = 20
    BACKOFF = 30
    STOPPING = 40
    EXITED = 100
    FATAL = 200
    UNKNOWN = 1000


# ===============================
# SERVICE ADMIN (SAFE VERSION)
# ===============================

class ServiceAdmin:
    """Remote supervisor admin (VPN-safe)"""

    __instances = {}

    def __new__(cls, ip: str, port: int = 9001):
        idx = f"{ip}:{port}"
        if idx in cls.__instances:
            return cls.__instances[idx]
        instance = super().__new__(cls)
        cls.__instances[idx] = instance
        return instance

    def __init__(self, ip: str, port: int = 9001) -> None:
        self.__ip = ip
        self.__port = port
        self.__server = ServerProxy(
            f"http://{ip}:{port}/RPC2",
            transport=TimeoutTransport(timeout=5),
            allow_none=True,
        )

    # ---------- INTERNAL SAFE CALL ----------

    def _rpc(self, fn, *args):
        try:
            return fn(*args)
        except (socket.timeout, OSError):
            raise RuntimeError("Supervisor RPC timeout (VPN connection lost)")
        except Exception as e:
            raise RuntimeError(f"Supervisor RPC error: {e}") from e

    # ---------- PUBLIC API ----------

    def get_all_services(self) -> List[str]:
        data = self._rpc(self.__server.supervisor.getAllProcessInfo)
        return [p["name"] for p in data]

    def get_service_state(self, name: str) -> ServiceState:
        info = self._rpc(self.__server.supervisor.getProcessInfo, name)
        return ServiceState(info.get("state", ServiceState.UNKNOWN.value))

    def get_service_state_name(self, name: str) -> str:
        info = self._rpc(self.__server.supervisor.getProcessInfo, name)
        return info.get("statename", "UNKNOWN")

    # ---------- SAFE CONTROL ----------

    def stop_service(self, name: str, timeout: int = 15) -> None:
        start = time.time()

        while time.time() - start < timeout:
            state = self.get_service_state(name)

            if state == ServiceState.STOPPED:
                return

            if state in {
                ServiceState.RUNNING,
                ServiceState.STARTING,
                ServiceState.BACKOFF,
                ServiceState.EXITED,
                ServiceState.FATAL,
            }:
                self._rpc(self.__server.supervisor.stopProcess, name)

            time.sleep(0.5)

        raise TimeoutError(f"Timeout while stopping service: {name}")

    def start_service(self, name: str, timeout: int = 15) -> None:
        start = time.time()

        while time.time() - start < timeout:
            state = self.get_service_state(name)

            if state == ServiceState.RUNNING:
                return

            if state == ServiceState.STOPPED:
                self._rpc(self.__server.supervisor.startProcess, name)

            if state in {
                ServiceState.BACKOFF,
                ServiceState.EXITED,
                ServiceState.FATAL,
            }:
                raise RuntimeError(
                    f"{name} in unrecoverable state ({self.get_service_state_name(name)})"
                )

            time.sleep(0.5)

        raise TimeoutError(f"Timeout while starting service: {name}")

    def restart_service(self, name: str) -> None:
        self.stop_service(name)
        self.start_service(name)

    @classmethod
    def clear_instances(cls) -> None:
        cls.__instances.clear()


# ===============================
# RAW CLIENT (UNCHANGED + SAFE)
# ===============================

class RawClient:
    """Low-level client base with auto-recovery."""

    _exception_type: Exception
    _service_name: str

    REQUEST_RETRIES = 2       # koliko dodatnih poskusov po recoveryju
    RECOVERY_SLEEP = 3.0      # koliko počaka po restartu servisa
    
    def __init__(self, ip: str, port: int) -> None:
        self._ip = ip
        self._port = port
        self._client = RequestResponseClient(ip, port)

    def __del__(self) -> None:
        try:
            self.disconnect()
        except Exception:
            pass


    def connect(self) -> None:
        self._client.connect()

    def disconnect(self) -> None:
        try:
            self._client.disconnect()
        except Exception:
            pass


    def _validate_response(
        self, request: Dict[str, Any], response: Dict[str, Any]
    ) -> None:
        """Validate service response."""
        if not isinstance(response, dict):
            raise self._exception_type(
                f"Invalid response type for request {request!r}: "
                f"{type(response).__name__} -> {response!r}"
            )

        if response.get("status") != "OK":
            msg = response.get("msg", SERVER_ERROR_STR)
            raise ValueError(f"{request!r} failed:\n###{msg}###")

    def _should_recover_from_exception(self, exc: Exception) -> bool:
        """Return True if exception looks like transport / service failure."""
        if isinstance(exc, (TimeoutError, OSError, ConnectionError)):
            return True

        msg = str(exc)
        recoverable_tokens = (
            "Timed out while waiting for response",
            "Request failed after",
            "Connection reset by peer",
            "forcibly closed by the remote host",
            "Broken pipe",
            "timed out",
            "WinError 10054",
        )
        return any(token in msg for token in recoverable_tokens)

    def _wait_for_service_port(self, timeout: float = 20.0, interval: float = 0.5) -> None:
        """Wait until remote TCP port starts accepting connections."""
        deadline = time.time() + timeout
        last_exc = None

        while time.time() < deadline:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            try:
                sock.connect((self._ip, self._port))
                sock.close()
                return
            except Exception as exc:
                last_exc = exc
                time.sleep(interval)
            finally:
                try:
                    sock.close()
                except Exception:
                    pass

        raise RuntimeError(
            f"Service '{self._service_name}' on {self._ip}:{self._port} "
            f"did not start listening within {timeout}s: {last_exc}"
        )

    def _recover_service_connection(self) -> None:
        """Disconnect, restart remote service via supervisor, wait for port, reconnect."""
        try:
            self.disconnect()
        except Exception:
            pass

        service_name = getattr(self, "_service_name", None)
        if service_name:
            try:
                ServiceAdmin.clear_instances()
            except Exception:
                pass

            admin = ServiceAdmin(self._ip)
            admin.restart_service(service_name)

            # Wait a bit for process bootstrap
            time.sleep(self.RECOVERY_SLEEP)

            # Wait until service really listens on TCP port
            self._wait_for_service_port(timeout=20.0, interval=0.5)

        self.connect()

    def _request(self, request, retry: int = None) -> Serializable:
        """Execute request with auto-recovery on timeout/reset/network errors."""
        if retry is None:
            retry = self.REQUEST_RETRIES

        last_exc = None

        for attempt in range(retry + 1):
            try:
                response = self._client.request(request)
                self._validate_response(request, response)
                return response

            except Exception as exc:
                last_exc = exc

                # Recovery samo za mrežne / transportne težave
                if not self._should_recover_from_exception(exc):
                    raise
                

                # Ni več retryjev -> končaj
                if attempt >= retry:
                    break

                try:
                    print(
                        f"[WARN] Recovering service '{self._service_name}' "
                        f"on {self._ip}:{self._port} after error: {exc}"
                    )
                    self._recover_service_connection()
                except Exception as recover_exc:
                    raise RuntimeError(
                        f"Failed to recover service '{self._service_name}' "
                        f"on {self._ip}:{self._port} after request {request!r}: "
                        f"{recover_exc}"
                    ) from recover_exc

        raise RuntimeError(
            f"Request {request!r} failed after {retry + 1} attempt(s) "
            f"for service '{self._service_name}' on {self._ip}:{self._port}: "
            f"{last_exc}"
        ) from last_exc

    def _get_request(
        self, request: Dict[str, Any]
    ) -> Union[str, int, float, list, dict, None]:
        response = self._request(request)
        if not isinstance(response, dict):
            raise self._exception_type(
                f"Invalid response type for get request {request!r}: "
                f"{type(response).__name__} -> {response!r}"
            )

        if "value" not in response:
            raise self._exception_type(SERVER_ERROR_STR)

        return response["value"]

