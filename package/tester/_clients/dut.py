"""Device Under Test client"""
import re
from typing import Any, Dict, Iterable, List, Tuple

import stream
import stream.byte
import stream.coder
import stream.packer
import stream.specializations.inspector
import stream.specializations.hisense
import stream.topic

from .templates import ATTR_GROUP, ATTR_MODE, ATTR_VALUE, MODE_GET, MODE_SET, RawClient


class StreamStack(stream.StreamStack):
    """`stream`'s StreamStack whish supports construction from string pipeline and list
    of named parameters
    """

    STREAM_CLASSES = {
        "serial": stream.byte.SerialStream,
        "socket": stream.byte.TCPStream,
        "packer": stream.packer.PackerStream,
        "coder": stream.coder.CoderStream,
        "topic": stream.topic.ByteTopicStream,
        "inspector": stream.specializations.inspector.InspectorStream,
        "hisense": stream.specializations.hisense.HisenseStrem
    }
    STREAM_CLASS_PARAMS = {
        "packer": {
            "hisense": stream.packer.HisensePacker,
            "termination": stream.packer.TerminationPacker,
        },
        "coder": {"checksum": stream.coder.CheckSumCoder, "crc": stream.coder.CRCCoder},
    }

    @classmethod
    def from_pipeline(
        cls, pipeline: str, parameters: List[Dict[str, Any]]
    ) -> "StreamStack":
        """Constructs a StreamStack object from string

        This is a preferred way of constructing a new SerialStream object.
        The newly constructed stream stack is not opened.

        :param pipeline: string representation of a pipeline
        :param parameters: a list of each underlying stream's parameters
        :return: newly constructed StreamStack object
        """
        class_parameters = []
        for stream_string, kwargs in zip(
            map(lambda s: s.strip(), pipeline.split("|")), parameters
        ):
            stream, parameter = re.match(
                r"^([a-z\_]*)(?:\(([a-z\_]*)\))?", stream_string
            ).groups()
            stream_tuple = (
                cls.STREAM_CLASSES[stream],
                (cls.STREAM_CLASS_PARAMS[stream][parameter],)
                if parameter is not None
                else tuple(),
                kwargs,
            )
            class_parameters.append(stream_tuple)
        return cls(class_parameters)


GROUP_OPEN = "open"
GROUP_INFO = "info"
GROUP_CONFIG = "config"


class DUTServiceError(Exception):
    """Type to indicate the DUT service error"""


class DUT(RawClient):
    """Device Under Test Client class

    :param ip: ip address of the device, running DUT service
    :param port: port of the DUT service, defaults to 50001
    """

    _exception_type = DUTServiceError  #:
    _service_name = "dut_service"  #:

    def __init__(self, ip: str, port: int = 50001) -> None:
        """Initializes Device Under Test object"""
        super().__init__(ip, port)
        self._ip = ip

    @property
    def bridges_opened(self) -> bool:
        """Observe or control whether the bridged connections are active

        :raises DUTServiceError: in case not all bridges share the same state
        :return: bridges state
        """
        states = self._get_request({ATTR_GROUP: GROUP_OPEN, ATTR_MODE: MODE_GET})
        state = all(states)
        if any(states) and not state:
            raise DUTServiceError("Bridges are in non consistent state")
        return state

    @bridges_opened.setter
    def bridges_opened(self, value: bool) -> None:
        """Bridges state setter

        :param value: desired bridges state
        """
        self._request({ATTR_GROUP: GROUP_OPEN, ATTR_MODE: MODE_SET, ATTR_VALUE: value})

    @property
    def info(self) -> List[Dict[str, str]]:
        """Bridges' info

        :return: a collection of information dicts
        """
        return self._get_request({ATTR_GROUP: GROUP_INFO, ATTR_MODE: MODE_GET})

    def configure_ports(self, data: List[Dict[str, int]]) -> None:
        """Configures com ports on the remote device

        :param data: a list of configuration parameters for each port

        A configuration parameter is a dictionary with key-value pairs.
        May be empty if no change to port is desired.
        Supported keys:
        * baudrate
        """
        return self._request(
            {ATTR_GROUP: GROUP_CONFIG, ATTR_MODE: MODE_SET, ATTR_VALUE: data}
        )

    def get_streams(
        self, stream_data: Iterable[Tuple[str, List[Dict[str, Any]]]]
    ) -> Tuple[StreamStack]:
        """Constructs streams from given stream data

        :param stream_data: stream data to construct streams from
        :raises ValueError: in case of insufficient number of active bridges
        :return: a collection of constructed stream objects
        """
        self.bridges_opened = False
        config = [parameters[0] for _, parameters in stream_data]
        missing_configs = len(self.info) - len(config)
        if missing_configs < 0:
            raise ValueError(
                "not enough serial bridges available. See dut_config at test point."
            )
        config.extend([{}] * missing_configs)
        self.configure_ports(config)
        ports = [info["socket_port"] for info in self.info]
        ret = tuple(
            StreamStack.from_pipeline(
                pipeline, [{"ip": self._ip, "port": port}, *parameters[1:]]
            )
            for (pipeline, parameters), port in zip(stream_data, ports)
        )
        return ret
