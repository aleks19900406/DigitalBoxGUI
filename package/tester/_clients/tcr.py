"""Test cell robot client"""
from enum import Enum
from math import pi
from numbers import Real
from time import sleep
from typing import Any, Dict, List, Tuple, Union, cast

from tester._common.defines import (
    ATTR_ACCELERATION,
    ATTR_FORCE,
    ATTR_PERCENTAGE,
    ATTR_SPEED,
)
from tester.helpers.imaging.geometry import Transformation

from .templates import (
    ATTR_GROUP,
    ATTR_MODE,
    ATTR_SUBGROUP,
    ATTR_VALUE,
    MODE_GET,
    MODE_SET,
    RawClient,
)

GROUP_POSE = "pose"
GROUP_MOVE = "move"
GROUP_TOOL = "tool"
GROUP_GRIP = "grip"
GROUP_SPINNER = "spinner"
GROUP_SAFETY = "safety"
GROUP_ORIGIN = "origin"
GROUP_SHORTCUTS = "shortcuts"

SUBGROUP_POSE = GROUP_POSE
SUBGROUP_WRIST = "wrist"
SUBGROUP_TYPE = "type"
SUBGROUP_SPEED_JOINT = "speedJ"
SUBGROUP_SPEED_LINEAR = "speedL"
SUBGROUP_ACCELERATION_JOINT = "accelJ"
SUBGROUP_ACCELERATION_LINEAR = "accelL"
SUBGROUP_STATE = "state"
SUBGROUP_ACTIVE = "active"
SUBGROUP_PERCENTAGE = "percentage"
SUBGROUP_FORCE = "force"
SUBGROUP_SPEED = "speed"
SUBGROUP_HAS_OBJECT = "has_object"
SUBGROUP_ERROR_CODE = "ec"
SUBGROUP_DOOR = "door"
SUBGROUP_SCRIPT = "script"
SUBGROUP_ORIGIN_USER = "user"
SUBGROUP_UNTIE = "untie"

WRIST_MAX = pi
WRIST_MIN = -pi
WRIST_RANGE = WRIST_MAX - WRIST_MIN


class TCRServiceError(Exception):
    """Type to indicate the TCR service error"""


class TCRException(Exception):
    """Type to indicate the TCR error"""


# ******************** ENUMS ********************
class JsonEnum(Enum):
    """JsonEnum base class"""

    def to_json(self) -> Union[str, int]:
        """Returns json representation of an Enum value"""
        return self.value


class Tool(JsonEnum):
    """Available robot tools"""

    NEEDLE = "needle"
    GRIP = "grip"
    FINGER = "finger"
    SPINNER = "spinner"
    CAMERA = "camera"


class Grip(JsonEnum):
    """Available gripper states"""

    CLOSED = "closed"
    OPENED = "opened"


class MoveType(JsonEnum):
    """Available movement types"""

    LINEAR = "linear"
    JOINT = "joint"
    WRIST = "wrist"
    UNTIE = "untie"
    FREEDRIVE = "free"


class MoveState(JsonEnum):
    """Available movement states"""

    STEADY = "steady"
    MOVING = "moving"
    BLOCKED = "blocked"
    FREE = "free"

    def __bool__(self) -> bool:
        if self == MoveState.BLOCKED:
            return False
        return True


class Spinner(JsonEnum):
    """Available spinner states"""

    OFF = "off"
    ON = "on"


class DoorState(JsonEnum):
    """Available door states"""

    CLOSED = True
    OPENED = False


class ScriptState(JsonEnum):
    """Available script states"""

    RUNNING = True
    STOPPED = False


class Origin(JsonEnum):
    """Available robot origins"""

    ROBOT = "robot"
    TOOL = "tool"
    USER = "user"


# ******************** CELL ROBOT CLASS ********************
class TCR(RawClient):
    """Test cell robot class"""

    _exception_type = TCRServiceError  #:
    _service_name = "tcr_service"  #:

    # TODO: This should probably be given by the service:
    spinner_diameter = 30

    def __init__(self, ip: str, port: int = 50004) -> None:
        """Initializes Robot object

        :param ip: ip addres of device, running TCR service
        :param port: port of the TCR service, defaults to 50004
        """
        super(TCR, self).__init__(ip, port)

    @property
    def pose(self) -> List[float]:
        """Tool Center Point represents the tool's pose in the robot's
        origin.

        Pose is a list of six floats.
        The first half represents translation and the second orientation.
        """
        return cast(
            List[float],
            self._get_request(
                {
                    ATTR_GROUP: GROUP_POSE,
                    ATTR_SUBGROUP: SUBGROUP_POSE,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @pose.setter
    def pose(self, value: List[float]) -> None:
        """Set robot's TCP based on currently active robot's origin

        :param value: desired Tool Center Point
        """
        self._request(
            {
                ATTR_GROUP: GROUP_POSE,
                ATTR_SUBGROUP: SUBGROUP_POSE,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: value,
            }
        )

    @property
    def wrist(self) -> float:
        """The rotation angle for the last wrist joint to enable object
        rotation"""
        return cast(
            float,
            self._get_request(
                {
                    ATTR_GROUP: GROUP_POSE,
                    ATTR_SUBGROUP: SUBGROUP_WRIST,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @wrist.setter
    def wrist(self, angle: float) -> None:
        """Set the wrist angle

        :param angle: absolute angle of rotation
        """
        self._request(
            {
                ATTR_GROUP: GROUP_POSE,
                ATTR_SUBGROUP: SUBGROUP_WRIST,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: angle,
            }
        )

    @property
    def move_type(self) -> MoveType:
        """Currently active move type

        :return: active move type
        """
        return MoveType(
            self._get_request(
                {
                    ATTR_GROUP: GROUP_MOVE,
                    ATTR_SUBGROUP: SUBGROUP_TYPE,
                    ATTR_MODE: MODE_GET,
                }
            )
        )

    @move_type.setter
    def move_type(self, move_type: MoveType) -> None:
        """Set desired move type

        :param move_type: desired move type
        """
        self._request(
            {
                ATTR_GROUP: GROUP_MOVE,
                ATTR_SUBGROUP: SUBGROUP_TYPE,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: move_type.to_json(),
            }
        )

    @property
    def move_joint_speed(self) -> float:
        """Active joint speed

        :return: active joint speed
        """
        return cast(
            float,
            self._get_request(
                {
                    ATTR_GROUP: GROUP_MOVE,
                    ATTR_SUBGROUP: SUBGROUP_SPEED_JOINT,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @move_joint_speed.setter
    def move_joint_speed(self, speed: float) -> None:
        """Set desired joint speed

        :param speed: desired joint speed
        """
        self._request(
            {
                ATTR_GROUP: GROUP_MOVE,
                ATTR_SUBGROUP: SUBGROUP_SPEED_JOINT,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: speed,
            }
        )

    @property
    def move_linear_speed(self) -> float:
        """Active linear speed

        :return: active linear speed
        """
        return cast(
            float,
            self._get_request(
                {
                    ATTR_GROUP: GROUP_MOVE,
                    ATTR_SUBGROUP: SUBGROUP_SPEED_LINEAR,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @move_linear_speed.setter
    def move_linear_speed(self, speed: float) -> None:
        """Set desired linear speed

        :param speed: desired linear speed
        """
        self._request(
            {
                ATTR_GROUP: GROUP_MOVE,
                ATTR_SUBGROUP: SUBGROUP_SPEED_LINEAR,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: speed,
            }
        )

    @property
    def move_joint_accel(self) -> float:
        """Active joint acceleration

        :return: active joint acceleration
        """
        return cast(
            float,
            self._get_request(
                {
                    ATTR_GROUP: GROUP_MOVE,
                    ATTR_SUBGROUP: SUBGROUP_ACCELERATION_JOINT,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @move_joint_accel.setter
    def move_joint_accel(self, accel: float) -> None:
        """Set desired joint acceleration

        :param speed: desired joint acceleration
        """
        self._request(
            {
                ATTR_GROUP: GROUP_MOVE,
                ATTR_SUBGROUP: SUBGROUP_ACCELERATION_JOINT,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: accel,
            }
        )

    @property
    def move_linear_accel(self) -> float:
        """Active linear acceleration

        :return: active linear acceleration
        """
        return cast(
            float,
            self._get_request(
                {
                    ATTR_GROUP: GROUP_MOVE,
                    ATTR_SUBGROUP: SUBGROUP_ACCELERATION_LINEAR,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @move_linear_accel.setter
    def move_linear_accel(self, accel: float) -> None:
        """Set desired linear acceleration

        :param speed: desired linear acceleration
        """
        self._request(
            {
                ATTR_GROUP: GROUP_MOVE,
                ATTR_SUBGROUP: SUBGROUP_ACCELERATION_LINEAR,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: accel,
            }
        )

    @property
    def move_state(self) -> MoveState:
        """Active move state

        :return: active move state
        """
        return MoveState(
            self._get_request(
                {
                    ATTR_GROUP: GROUP_MOVE,
                    ATTR_SUBGROUP: SUBGROUP_STATE,
                    ATTR_MODE: MODE_GET,
                }
            )
        )

    @move_state.setter
    def move_state(self, state: MoveState) -> None:
        """Set desired move state

        :param state: desired move state
        """
        self._request(
            {
                ATTR_GROUP: GROUP_MOVE,
                ATTR_SUBGROUP: SUBGROUP_STATE,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: state.to_json(),
            }
        )

    @property
    def tool(self) -> Tool:
        """Robot's active tool

        :return: active robot's tool

        .. note::
            Use :meth:`TCR.change_tool` to change tool.
        """
        return Tool(
            self._get_request(
                {
                    ATTR_GROUP: GROUP_TOOL,
                    ATTR_SUBGROUP: SUBGROUP_ACTIVE,
                    ATTR_MODE: MODE_GET,
                }
            )
        )

    @tool.setter
    def tool(self, value: Tool) -> None:
        """Set robot's active tool

        :param value: string representation of one of robot's availabe tools
        """
        self._request(
            {
                ATTR_GROUP: GROUP_TOOL,
                ATTR_SUBGROUP: SUBGROUP_ACTIVE,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: value.to_json(),
            }
        )

    @property
    def grip_state(self) -> Grip:
        """Active gripper's state

        :return: active gripper's state
        """
        return Grip(
            self._get_request(
                {
                    ATTR_GROUP: GROUP_GRIP,
                    ATTR_SUBGROUP: SUBGROUP_STATE,
                    ATTR_MODE: MODE_GET,
                }
            )
        )

    @grip_state.setter
    def grip_state(self, state: Grip) -> None:
        """Set desired grip's state

        :param state: desired grip state
        """
        self._request(
            {
                ATTR_GROUP: GROUP_GRIP,
                ATTR_SUBGROUP: SUBGROUP_STATE,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: state.to_json(),
            }
        )

    @property
    def grip_percentage(self) -> int:
        """Active gripper's closed percentage

        :return: active gripper's closed percentage

        Gripper percentage is valid in range 0-100
        """
        return cast(
            int,
            self._get_request(
                {
                    ATTR_GROUP: GROUP_GRIP,
                    ATTR_SUBGROUP: SUBGROUP_PERCENTAGE,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @grip_percentage.setter
    def grip_percentage(self, value: int) -> None:
        """Set desired gripper's closed percentage

        :param value: desired gripper's closed percentage

        Gripper percentage is valid in range 0-100
        """
        self._request(
            {
                ATTR_GROUP: GROUP_GRIP,
                ATTR_SUBGROUP: SUBGROUP_PERCENTAGE,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: value,
            }
        )

    @property
    def grip_force(self) -> int:
        """Active gripper's force

        :return: active gripper's force

        Gripper force is valid in range 0-255
        """
        return cast(
            int,
            self._get_request(
                {
                    ATTR_GROUP: GROUP_GRIP,
                    ATTR_SUBGROUP: SUBGROUP_FORCE,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @grip_force.setter
    def grip_force(self, value: int) -> None:
        """Set desired gripper's force

        :param value: desired gripper's force

        Gripper force is valid in range 0-255
        """
        self._request(
            {
                ATTR_GROUP: GROUP_GRIP,
                ATTR_SUBGROUP: SUBGROUP_FORCE,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: value,
            }
        )

    @property
    def grip_speed(self) -> int:
        """Closing/opening gripper speed

        :return: active gripper's closing/opening speed

        Gripper speed is valid in range 0-255
        """
        return cast(
            int,
            self._get_request(
                {
                    ATTR_GROUP: GROUP_GRIP,
                    ATTR_SUBGROUP: SUBGROUP_SPEED,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @grip_speed.setter
    def grip_speed(self, speed: int) -> None:
        """Set desired closing/opening gripper speed

        :param speed: gripper speed

        Gripper speed is valid in range 0-255
        """
        self._request(
            {
                ATTR_GROUP: GROUP_GRIP,
                ATTR_SUBGROUP: SUBGROUP_SPEED,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: speed,
            }
        )

    @property
    def grip_has_object(self) -> bool:
        """Information about whether the gripper holds an object

        :return: True if gripper holds an object, else false
        """
        return cast(
            bool,
            self._get_request(
                {
                    ATTR_GROUP: GROUP_GRIP,
                    ATTR_SUBGROUP: SUBGROUP_HAS_OBJECT,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @property
    def spinner_state(self) -> Spinner:
        """Active spinner state

        :return: active spinner state
        """
        return Spinner(
            self._get_request(
                {
                    ATTR_GROUP: GROUP_SPINNER,
                    ATTR_SUBGROUP: SUBGROUP_STATE,
                    ATTR_MODE: MODE_GET,
                }
            )
        )

    @spinner_state.setter
    def spinner_state(self, state: Spinner) -> None:
        """Set desired spinner state

        :param state: desired spinner state
        """
        self._request(
            {
                ATTR_GROUP: GROUP_SPINNER,
                ATTR_SUBGROUP: SUBGROUP_STATE,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: state.to_json(),
            }
        )

    @property
    def spinner_speed(self) -> int:
        """Active spinner speed

        :return: active spinner speed
        """
        return cast(
            int,
            self._get_request(
                {
                    ATTR_GROUP: GROUP_SPINNER,
                    ATTR_SUBGROUP: SUBGROUP_SPEED,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @spinner_speed.setter
    def spinner_speed(self, speed: int) -> None:
        """Set desired spinner speed

        :param speed: desired spinner speed
        """
        self._request(
            {
                ATTR_GROUP: GROUP_SPINNER,
                ATTR_SUBGROUP: SUBGROUP_SPEED,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: speed,
            }
        )

    @property
    def error_code(self) -> List[Tuple[int, str]]:
        """Get robot's error code

        :return: robot's error code
        """
        return cast(
            List[Tuple[int, str]],
            self._get_request(
                {
                    ATTR_GROUP: GROUP_SAFETY,
                    ATTR_SUBGROUP: SUBGROUP_ERROR_CODE,
                    ATTR_MODE: MODE_GET,
                }
            ),
        )

    @property
    def door_state(self) -> DoorState:
        """Get test cell's door state

        :return: test cell's door state
        """
        return DoorState(
            self._get_request(
                {
                    ATTR_GROUP: GROUP_SAFETY,
                    ATTR_SUBGROUP: SUBGROUP_DOOR,
                    ATTR_MODE: MODE_GET,
                }
            )
        )

    @property
    def script_state(self) -> ScriptState:
        """Robot's script state

        :return: True if script is running else False
        """
        return ScriptState(
            self._get_request(
                {
                    ATTR_GROUP: GROUP_SAFETY,
                    ATTR_SUBGROUP: SUBGROUP_SCRIPT,
                    ATTR_MODE: MODE_GET,
                }
            )
        )

    @property
    def user_origin(self) -> List[List[float]]:
        """Robot's user-defined origin

        :raises NotImplementedError: Getting user-defined origin is not
                                     possible
        """
        raise NotImplementedError("Reading origin is not implemented")

    @user_origin.setter
    def user_origin(self, value: List[List[float]]) -> None:
        """Set new robot's origin coordinate system

        :param value: new robot's origin

        List of translation values of three points::

            point1 = [0, 0, 10]
            point2 = [10, 10, 10]
            point3 = [-10, 10, 10]
            [point1, point2, point3]
        """
        self._request(
            {
                ATTR_GROUP: GROUP_ORIGIN,
                ATTR_SUBGROUP: SUBGROUP_ORIGIN_USER,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: value,
            }
        )

    @property
    def origin_type(self) -> Origin:
        """Active robot's origin tpe

        :return: active origin type
        """
        return Origin(
            self._get_request(
                {
                    ATTR_GROUP: GROUP_ORIGIN,
                    ATTR_SUBGROUP: SUBGROUP_TYPE,
                    ATTR_MODE: MODE_GET,
                }
            )
        )

    @origin_type.setter
    def origin_type(self, value: Origin) -> None:
        """Set active robot's origin type

        :param value: desired origin type
        """
        self._request(
            {
                ATTR_GROUP: GROUP_ORIGIN,
                ATTR_SUBGROUP: SUBGROUP_TYPE,
                ATTR_MODE: MODE_SET,
                ATTR_VALUE: value.to_json(),
            }
        )

    def _get_grip_delay(self, speed: int, percentage: int) -> float:
        delay = 0.5  # Delayed response in seconds
        # f1 practically represents real speed when speed attribute is set to 0
        f1 = 0.04111111111111111
        f2 = 0.00015  # f2 represents speed correction factor
        return percentage * (f1 - f2 * speed) + delay

    def untie(self) -> None:
        """Immediately cancels all execution and moves to neutral position"""
        self._request(
            {
                ATTR_GROUP: GROUP_SHORTCUTS,
                ATTR_SUBGROUP: SUBGROUP_UNTIE,
                ATTR_MODE: MODE_SET,
            }
        )

    def start_freedrive(self) -> None:
        """Sets robot in freedrive mode"""
        self.move_type = MoveType.FREEDRIVE
        self.move_state = MoveState.FREE

    def end_freedrive(self) -> None:
        """Cancels freedrive mode"""
        self.move_state = MoveState.BLOCKED

    def change_tool(self, tool: Tool) -> None:
        """Tool change shortcut

        :param tool: desired tool to activate

        .. note::
            Use instead of :meth:`TCR.tool`.
        """
        if tool is not self.tool:
            self.move_state = MoveState.BLOCKED
            self.tool = tool
            self.pose = self.pose

    def move(
        self,
        pose: Union[Tuple[float, float, float, float, float, float], float],
        move_type: MoveType = None,
        origin: Origin = None,
        speed: float = None,
        accel: float = None,
    ) -> None:
        """Move shortcut

        .. note::
            All arguments but pose are by default the currently active values
            on robot.
        .. note::
            All passed arguments are applied to the robot and overwrite the
            current previous settings.

        :param pose: new desired pose
        :param move_type: desired movement type
        :param origin: desired origin to perform a movement in relation to
        :param speed: desired movement speed
        :param accel: desired movement acceleration
        """
        if move_type:
            self.move_type = move_type
        else:
            move_type = self.move_type
        if move_type not in {MoveType.LINEAR, MoveType.JOINT, MoveType.WRIST}:
            raise TCRServiceError("invalid movement type")
        elif move_type is MoveType.WRIST and not isinstance(pose, Real):
            raise TCRServiceError("MoveType WRIST pose must be a number")
        elif move_type is not MoveType.WRIST and not isinstance(pose, (list, tuple)):
            raise TCRServiceError("MoveType JOINT and LINEAR pose must be list")
        try:
            self.move_state = MoveState.BLOCKED
            if origin:
                self.origin_type = origin
            if move_type is MoveType.LINEAR:
                if speed:
                    self.move_linear_speed = speed
                if accel:
                    self.move_linear_accel = accel
            else:
                if speed:
                    self.move_joint_speed = speed
                if accel:
                    self.move_joint_accel = accel
            if move_type is MoveType.WRIST:
                self.wrist = pose
            else:
                self.pose = pose
            sleep(0.02)
            self.move_state = MoveState.FREE
            sleep(0.04)
            while self.move_state == MoveState.MOVING:
                sleep(0.02)
            if self.error_code[0][0]:
                raise TCRException(f"Unable to move due to error: {self.error_code}")
        finally:
            self.move_state = MoveState.BLOCKED

    def grab(
        self,
        force: int = 0,
        percentage: int = 100,
        speed: int = 100,
        should_grab: bool = True,
        ignore_closed: bool = False,
    ) -> None:
        """Grab shortcut

        :param force: gripper grab force, defaults to 0
        :param percentage: gripper closed percentage, defaults to 100
        :param speed: gripper closing speed
        :param should_grab: whether it is mandatory for gripper to grab an
                            object, defaults to True
        :param ignore_closed: whether it is acceptable for the gripper to be already
                              closed
        :raises TCRException: if gripper is already closed and ignore_closed is False
        :raises TCRException: if *should_grab* and if no object is detected
                              when closed
        """
        if self.grip_state == Grip.CLOSED:
            if not ignore_closed:
                raise TCRException("grip is closed; open it first")
            else:
                return
        self.grip_force = force
        self.grip_percentage = percentage
        self.grip_speed = speed
        self.grip_state = Grip.CLOSED
        sleep(self._get_grip_delay(speed, percentage))
        if should_grab:
            sleep(0.3)
            if not self.grip_has_object:
                self.grip_state = Grip.OPENED
                raise TCRException("no object to grab")

    def release(self, speed: int = 255) -> None:
        """Release shortcut

        :param speed: gripper opening speed
        """
        try:
            if self.grip_state == Grip.CLOSED:
                percentage = self.grip_percentage
                self.grip_speed = speed
                self.grip_state = Grip.OPENED
                sleep(self._get_grip_delay(speed, percentage))
        except ValueError:
            self.grip_state = Grip.OPENED

    def rotate(
        self,
        angle: float,
        steps: int = 1,
        grab_sett: Dict[str, Any] = None,
        move_sett: Dict[str, Any] = None,
    ) -> None:
        """Rotate shortcut

        :param angle: desired step rotation angle
        :param steps: desired number of steps, defaults to 1
        :param grab_sett: *grab* method settings, defaults to None
        :param move_sett: *move* method settings, defaults to None
        :raises ValueError: in case an angle is too wide or too narrow
        :raises TCRException: in case the gripper is not a selected tool
        """
        if self.tool != Tool.GRIP:
            raise TCRException(
                "in order to rotate, the grip must be selected as active tool"
            )
        abs_angle = abs(angle)
        if abs_angle > (WRIST_RANGE):
            raise ValueError("given angle is too wide")
        elif abs_angle < 0.002:
            raise ValueError("given angle is too narrow")
        gs = {ATTR_FORCE: 0, ATTR_PERCENTAGE: 100, ATTR_SPEED: 100}
        gs.update(grab_sett if grab_sett is not None else {})
        ms = {ATTR_SPEED: 20, ATTR_ACCELERATION: 20}
        ms.update(move_sett if move_sett is not None else {})
        self.origin_type = Origin.ROBOT
        self.move_state = MoveState.BLOCKED
        self.move_type = MoveType.WRIST
        wrist = self.wrist
        # Synchronize wrist read/write register in order to disable movement after
        # MoveState.FREE
        self.wrist = wrist
        wrist_init = wrist
        sleep(0.02)
        positive = angle > 0
        simultaneous_steps = int((WRIST_MAX - WRIST_MIN) / abs_angle)
        while steps:
            avail_angle = abs(WRIST_MAX - wrist) if positive else abs(wrist - WRIST_MIN)
            avail_steps = int(avail_angle / abs_angle)
            if steps > avail_steps:
                wrist = WRIST_MIN if positive else WRIST_MAX
                self.release()
                self.move(wrist, MoveType.WRIST, **ms)
                avail_steps = simultaneous_steps
            steps_to_move = steps if steps < avail_steps else avail_steps
            steps -= steps_to_move
            if steps_to_move:
                wrist = wrist + steps_to_move * angle
                self.grab(**gs)
                self.move(wrist)
        self.release()
        self.move(wrist_init, MoveType.WRIST, **ms)

    def push(
        self,
        dist: float,
        count: int = 1,
        speed: float = 300,
        accel: float = 900,
        hold: float = 0,
    ) -> None:
        """Execute a push in positive z axis of a tool origin

        :param dist: distance of a push in mm
        :param count: number of executions, defaults to 1
        :param speed: movement speed, defaults to 300
        :param accel: movement acceleration, defaults to 900
        :param hold: time to hold
        """
        self.move_state = MoveState.BLOCKED
        self.move_type = MoveType.LINEAR
        self.move_linear_speed = speed
        self.move_linear_accel = accel
        self.origin_type = Origin.ROBOT
        pose = self.pose
        pose_delta = Transformation.from_pose((0, 0, -dist, 0, 0, 0))
        pose_below = Transformation.from_pose(pose).dot(pose_delta).to_pose()
        sleep(0.02)
        self.pose = pose_below
        self.move_state = MoveState.FREE
        for _ in range(count):
            self.pose = pose_below
            sleep(0.04)
            while self.move_state == MoveState.MOVING:
                sleep(0.02)
            sleep(hold)
            self.pose = pose
            sleep(0.04)
            while self.move_state == MoveState.MOVING:
                sleep(0.02)
