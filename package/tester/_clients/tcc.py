"""Test Cell Camera client"""
import socket
from typing import List, Tuple

import cv2
import numpy as np

from tester._common.defines import ATTR_DATA
from tester.helpers.imaging.geometry import Transformation, Transformation2d
from tester.helpers.imaging.objects import ROI
from tester.helpers.imaging.shot import Camera, Shot
from stream import byte

from .templates import (
    ATTR_GROUP,
    ATTR_MODE,
    ATTR_VALUE,
    IPV4_ALL,
    MODE_GET,
    MODE_SET,
    RawClient,
)

ATTR_ATTRIBUTE = "attr"
ATTR_POINTS = "points"
ATTR_RVEC = "rvec"
ATTR_TVEC = "tvec"

GROUP_IMAGE = "image"
GROUP_PATCHES = "patches"
GROUP_INTRINSIC_MATRIX = "intr"
GROUP_DISTORTION_COEFFICIENTS = "coef"
GROUP_NEW_INTRINSIC_MATRIX = "new_intr"
GROUP_REGION_OF_INTEREST = "roi"
GROUP_EXTRINSIC_CORRECTION = "extr"
GROUP_ATTRIBUTE = "attr"

DATA_ATTR_ADDRESS = "addr"
DATA_ATTR_PORT = "port"
DATA_ATTR_UNDISTORT = "undistort"


class _TCPStreamServer(byte.TCPStreamServer):
    def init(self) -> None:
        if self._server is None:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server.bind((self._ip, self._port))
            self._server.listen(1)
            self._server.settimeout(10)
        else:
            raise RuntimeError("Stream is already initialized")

    def _open_begin(self) -> None:
        if self._server is None:
            raise RuntimeError("Stream is not initialized")
        if self._socket is None:
            self._socket, _ = self._server.accept()
        else:
            raise RuntimeError("Stream is already opened")


class TCCServiceError(Exception):
    """Type to indicate the TCC service error"""


class TCC(RawClient, Camera):
    """Test Cell Camera Client class

    :param ip: ip address of device, running TCC service
    :param port: port of the TCC service, defaults to 50003
    """

    _exception_type = TCCServiceError  #:
    _service_name = "tcc_service"  #:

    def __init__(self, ip: str, port: int = 50003) -> None:
        """Initializes Test cell Camera object"""
        RawClient.__init__(self, ip, port)
        RawClient.connect(self)
        Camera.__init__(self, 3.45e-6, (4096, 3000))
        RawClient.disconnect(self)

    def _grab(self, undistort: bool, pose=None, calibrated=True) -> Shot:
        """Grab implementation"""
        data = {
            DATA_ATTR_ADDRESS: self._client.interface,
            DATA_ATTR_PORT: 50011,
            DATA_ATTR_UNDISTORT: undistort,
        }
        request = {ATTR_GROUP: GROUP_IMAGE, ATTR_MODE: MODE_GET, ATTR_DATA: data}
        s = _TCPStreamServer(IPV4_ALL, data[DATA_ATTR_PORT])
        s.init()
        self._client.send_request(request)
        s.open()
        try:
            pkg = self._receive_image(s)
        finally:
            s.close()
            response = self._client.recv_response()
            self._validate_response(request, response)
        array = np.frombuffer(pkg, dtype=np.uint8)
        return Shot(cv2.imdecode(array, 1), pose, self if calibrated else None)

    def grab(self, pose: Tuple[float] = None, calibrated: bool = True) -> Shot:
        """Grab distorted image

        :param pose: current tool pose, defaults to None
        :return: grabbed image
        """
        return self._grab(False, pose, calibrated)

    def grab_undistorted(self, pose: Tuple[float] = None) -> Shot:
        """Grab undistorted image

        :param pose: current tool pose, defaults to None
        :return: grabbed and undistorted image
        """
        return self._grab(True, pose)

    def _receive_image(self, s: _TCPStreamServer) -> bytes:
        endian = {b"\x00": "little", b"\x01": "big"}[bytes(s.read(1))]
        size_t_size = int.from_bytes(s.read(1), endian)
        to_read = int.from_bytes(s.read(size_t_size), endian, signed=False)
        pkg = b""
        while len(pkg) != to_read:
            pkg += s.read(to_read - len(pkg))
        return pkg

    def grab_patches(
        self, points: List[List[List[float]]], pose: List[float]
    ) -> List[np.ndarray]:
        """Grab undistorted image patches

        :param points: list of 3D point list to be used for patch extraction
        :param pose: camera pose in 3D space
        :return: list of image patches
        """
        trans = Transformation.from_pose(pose)
        data = {
            DATA_ATTR_ADDRESS: self._client.interface,
            DATA_ATTR_PORT: 50011,
        }
        request = {
            ATTR_GROUP: GROUP_PATCHES,
            ATTR_MODE: MODE_GET,
            ATTR_POINTS: points,
            ATTR_RVEC: trans.rotation_vector.tolist(),
            ATTR_TVEC: trans.translation.tolist(),
            ATTR_DATA: data,
        }
        s = _TCPStreamServer(IPV4_ALL, data[DATA_ATTR_PORT])
        s.init()
        self._client.send_request(request)
        try:
            s.open()
            pkgs = [self._receive_image(s) for _ in range(len(points))]
        finally:
            s.close()
            response = self._client.recv_response()
            self._validate_response(request, response)
        arrays = [np.frombuffer(pkg, dtype=np.uint8) for pkg in pkgs]
        return [cv2.imdecode(array, 1) for array in arrays]

    def _get_pixel_size(self) -> float:
        raise RuntimeError("this should've never been called")

    def _get_sensor_size_px(self) -> Tuple[int]:
        raise RuntimeError("this should've never been called")

    def _get_intrinsic_matrix(self) -> Transformation2d:
        l = self._get_request({ATTR_GROUP: GROUP_INTRINSIC_MATRIX, ATTR_MODE: MODE_GET})
        return np.array(l).reshape((3, 3)).view(Transformation2d)

    def _get_distortion_coefficients(self) -> Tuple:
        l = self._get_request(
            {ATTR_GROUP: GROUP_DISTORTION_COEFFICIENTS, ATTR_MODE: MODE_GET}
        )
        return tuple(l)

    def _get_new_intrinsic_matrix(self) -> Transformation2d:
        l = self._get_request(
            {ATTR_GROUP: GROUP_NEW_INTRINSIC_MATRIX, ATTR_MODE: MODE_GET}
        )
        return np.array(l).reshape((3, 3)).view(Transformation2d)

    def _get_undistorted_roi(self) -> ROI:
        l = self._get_request(
            {ATTR_GROUP: GROUP_REGION_OF_INTEREST, ATTR_MODE: MODE_GET}
        )
        return ROI.from_iterable(l)

    def _get_extrinsic_correction(self) -> Transformation:
        l = self._get_request(
            {ATTR_GROUP: GROUP_EXTRINSIC_CORRECTION, ATTR_MODE: MODE_GET}
        )
        return np.array(l).reshape((4, 4)).view(Transformation)

    def __getitem__(self, key: str) -> str:
        """Get desired camera attribute

        :param key: valid camera attribute
        :return: attribute value
        """
        return self._get_request(
            {ATTR_GROUP: GROUP_ATTRIBUTE, ATTR_MODE: MODE_GET, ATTR_ATTRIBUTE: key}
        )

    def __setitem__(self, key: str, value: str) -> None:
        """Set desired camera attribute

        :param key: valid camera attribute name
        :param value: desired attribute value
        """
        self._request(
            {
                ATTR_GROUP: GROUP_ATTRIBUTE,
                ATTR_MODE: MODE_SET,
                ATTR_ATTRIBUTE: key,
                ATTR_VALUE: value,
            }
        )
