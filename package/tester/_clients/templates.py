"""Client templates"""
from enum import Enum
from time import sleep
from typing import Any, Dict, List, Union
from xmlrpc.client import ServerProxy

from .request_response_client import RequestResponseClient, Serializable

SERVER_ERROR_STR = "something went wrong on service side - contact support!"

ATTR_GROUP = "group"
ATTR_SUBGROUP = "subgroup"
ATTR_MODE = "mode"
ATTR_VALUE = "value"

MODE_SET = "set"
MODE_GET = "get"

IPV4_ALL = "0.0.0.0"  #: All network interfaces
IPV4_LOCAL = "127.0.0.1"  #: Local network interface


class ServiceState(Enum):
    """Remote service state enum"""

    STOPPED = 0  #:
    STARTING = 10  #:
    RUNNING = 20  #:
    BACKOFF = 30  #:
    STOPPING = 40  #:
    EXITED = 100  #:
    FATAL = 200  #:
    UNKNOWN = 1000  #:


class ServiceAdmin:
    """Remote service admin

    Service admin uses XML-RPC API to control remote snd monitor service
    supervisor

    :param process: name of the process to control
    :param ip: service supervisor's remote address
    :param port: supervisor's port, defaults to 9001
    """

    __instances = {}

    __ip: str
    __port: int
    __server: ServerProxy

    def __new__(cls, ip: str, port: int = 9001) -> "ServiceAdmin":
        """Create service admin"""
        idx = f"{ip}:{port}"
        for i in cls.__instances:
            if i == idx:
                return cls.__instances[i]
        instance = super().__new__(cls)
        cls.__instances[idx] = instance
        return instance

    def __init__(self, ip: str, port: int = 9001) -> None:
        self.__ip = ip
        self.__port = port
        self.__server = ServerProxy(f"http://{ip}:{port}/RPC2")

    def get_all_services(self) -> List[str]:
        """Get all services' names"""
        return [i["name"] for i in self.__server.supervisor.getAllProcessInfo()]

    def get_service_state(self, name: str) -> ServiceState:
        """State of the monitoring process

        :param name: service's name
        :return: process' state
        """
        return ServiceState(self.__server.supervisor.getProcessInfo(name)["state"])

    def get_service_state_name(self, name: str) -> str:
        """State name of the monitoring process

        :param name: service's name
        :return: process' state name
        """
        return self.__server.supervisor.getProcessInfo(name)["statename"]

    def stop_service(self, name: str) -> None:
        """Stops the desired service

        :param name: service's name
        """
        state = self.get_service_state(name)
        avail_states = {
            ServiceState.STARTING,
            ServiceState.RUNNING,
            ServiceState.BACKOFF,
            ServiceState.EXITED,
            ServiceState.FATAL,
        }
        if state in avail_states:
            self.__server.supervisor.stopProcess(name)
            sleep(0.5)
            self.stop_service(name)
        elif state == ServiceState.STOPPING:
            sleep(0.5)
            self.stop_service(name)
        elif state == ServiceState.UNKNOWN:
            raise RuntimeError("supervisor is in invalid state")

    def start_service(self, name: str) -> None:
        """Starts the desired service

        :param name: service's name
        """
        state = self.get_service_state(name)
        if state in {ServiceState.STOPPING, ServiceState.STOPPED}:
            self.__server.supervisor.startProcess(name)
            sleep(0.5)
            self.start_service(name)
        elif state == ServiceState.STARTING:
            sleep(0.5)
            self.start_service(name)
        states = {ServiceState.BACKOFF, ServiceState.EXITED, ServiceState.FATAL}
        if state in states:
            raise RuntimeError(
                f"{name} is in unrecoverable state "
                + f"({self.get_service_state_name(name)})"
            )
        elif state == ServiceState.UNKNOWN:
            raise RuntimeError("supervisor is in invalid state")

    def restart_service(self, name: str) -> None:
        """Restarts the desired service

        :param name: service's name
        """
        self.stop_service(name)
        self.start_service(name)

    @classmethod
    def clear_instances(cls) -> None:
        """Clears all active instances"""
        cls.__instances.clear()


class RawClient:
    """Base client class that implements low level client functionality

    :param ip: ip address of the device, running service
    :param port: port of the service
    """

    _exception_type: Exception  #: Used for throwing on invalid response
    _service_name: str  #: used for ServiceAdmin

    def __init__(self, ip: str, port: int) -> None:
        """Initializes Client object"""
        self._client = RequestResponseClient(ip, port)

    def __del__(self) -> None:
        self.disconnect()

    def connect(self) -> None:
        """Connect to the server"""
        self._client.connect()

    def disconnect(self) -> None:
        """Disconnect from the server"""
        self._client.disconnect()

    def _validate_response(
        self, request: Dict[str, Any], response: Dict[str, Any]
    ) -> None:
        """Validates incoming response

        :param request: outgoing request
        :param response: incoming response
        :raises ValueError: in case the request failed
        :raises self._exception_type: in case of server error
        """
        try:
            if response["status"] != "OK":
                raise ValueError(
                    f"'{request}' request failed with message:" + f'\n{response["msg"]}'
                )
        except KeyError:
            raise self._exception_type(SERVER_ERROR_STR)

    def _request(self, request) -> Serializable:
        """Executes request to service

        :param request: command to be send to service
        :type request: dict
        :rtype: dict
        """
        response = self._client.request(request)
        self._validate_response(request, response)
        return response

    def _get_request(
        self, request: Dict[str, Any]
    ) -> Union[str, int, float, list, dict, None]:
        """Executes the get request to service and returns incoming value

        :param request: outgoing request
        :raises self._exception_type: in case of server error
        :return: response's value
        """
        response = self._request(request)
        self._validate_response(request, response)
        try:
            return response["value"]
        except KeyError:
            raise self._exception_type(SERVER_ERROR_STR)
