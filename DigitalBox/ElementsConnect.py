
import logging
from stream.byte import SerialStream
from stream.byte import TCPStream
from stream.packer import HisensePacker, PackerStream
from stream.coder import CheckSumCoder, CoderStream
from stream import StreamStack
import socket
import ctypes
from enum import Enum, auto
from time import sleep
from typing import  Union,Sequence, Tuple, Optional, List
SLEEP_AFTER_CMD = 0.03
MAX_RETRIES = 5  # how many times to try
# --- Helpers -----------------------------------------------------------------

def _bytes_hex(data: Union[bytes, bytearray]) -> str:
    """Return a space-separated hex string (e.g., '01 A4 0F')."""

# --- Data structures ---------------------------------------------------------
class CommandButton(ctypes.LittleEndianStructure):
    _pack_ = 1  # disable padding
    _fields_ = [("index", ctypes.c_uint8),
                ("type", ctypes.c_uint8)]

class CommandTouch(ctypes.LittleEndianStructure):
    _pack_ = 1  # disable padding
    _fields_ = [("coordinate_x", ctypes.c_uint16),
                ("coordinate_y", ctypes.c_uint16),
                ("type", ctypes.c_uint8)]
    
class Command(ctypes.LittleEndianStructure):
    _pack_ = 1  # disable padding
    _fields_ = [("value", ctypes.c_uint8)]

class CommandModel(ctypes.LittleEndianStructure):
    _pack_ = 1  # disable padding
    _fields_ = [("value", ctypes.c_uint32)]

class CommandType(Enum):

    BUTTON_PRESS = 1
    TOUCH_ACTION = auto()
    SET_MODEL = auto()
    GET_MODEL = auto()
    SET_LANGUAGE = auto()

class PressType(Enum):
    """Press types by hold time"""
    PRESSED = 1
    RELEASED = auto()
    MOVED = auto()     # :
    LONG_PRESS = auto()  # : ~3s
    
# --- DeviceConnection --------------------------------------------------------
class NoInfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno != logging.INFO
class DeviceConnection:

    def __init__(self, method: str = "wifi", **kwargs):
        self.logger = logging.getLogger(__name__)
        #self.logger.setLevel(logging.DEBUG)
        self.logger.setLevel(logging.WARNING)
        if method == "serial":
            SERIAL1_PARAMS = {"device": kwargs["comport"]}
            s = SerialStream(SERIAL1_PARAMS, kwargs.get("baudrate", 230400))
        elif method == "wifi":
            self.host = kwargs["host"]
            self.port = kwargs["port"]
            self.base_stream_params = (TCPStream, [self.host, self.port], {})
        else:
            raise ValueError("Unsupported connection method")

        # Create StreamStack
        self._create_stream_stack()

    def _create_stream_stack(self):
        """Create StreamStack from the base_stream_params"""
        self.his_protokol = StreamStack((
            self.base_stream_params,
            (PackerStream, [HisensePacker], {}),
        ))

    # ----------------- Pre-check if device is reachable -----------------
    def _is_device_reachable(self, host: str, port: int, timeout: float = 2.0) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    # ----------------- Connect with retries -----------------
    def connect(self, retries: int = 5, base_delay: float = 5.0):
        for attempt in range(1, retries + 1):
            # Recreate StreamStack fresh on each attempt
            self._create_stream_stack()

            # Wait until device is reachable (Wi-Fi only)
            if isinstance(self.base_stream_params[0], type) and self.base_stream_params[0] is TCPStream:
                wait_time = 0
                while not self._is_device_reachable(self.host, self.port):
                    sleep(1)
                    wait_time += 1
                    if wait_time > 10:
                        break

            # Try to open connection
            try:
                self.logger.debug(f"Attempt {attempt}/{retries} to connect...")
                self.his_protokol.open()
                sleep(2)
                self._connected = True
                self.logger.info("Connected to device.")
                return
            except Exception as e:
                self._connected = False
                delay = base_delay * attempt
                self.logger.warning(f"Connection failed on attempt {attempt}: {e}, retrying in {delay}s")
                sleep(delay)

        raise ConnectionError(f"Failed to connect after {retries} attempts.")


    def disconnect(self):
        """Idempotent disconnect using logging for status and errors."""
        try:
            self.his_protokol.close()
            sleep(2)
        except Exception as e:
            self.logger.error("Failed to disconnect.", exc_info=True)
            raise ConnectionError(f"Failed to disconnect: {e}")
        finally:
            self._connected = False
            self.logger.info("Disconnected from device.")

    def send(self, data: bytes):
        """Send raw data over active connection (serial or Wi-Fi)."""
        if isinstance(data, (bytes, bytearray)):
            data = [bytearray(data)]
        try:
            self.his_protokol.write(data)
            # Log only sizes/hex if useful. Here we log first frame for visibility.
            if data and isinstance(data[0], (bytes, bytearray)):
                self.logger.debug("Sent frame: %s", _bytes_hex(data[0]))
        except Exception:
            self.logger.error("Error while sending data.", exc_info=True)
            raise

    def recv(self, size: int = 1024) -> bytes:
        """Receive raw data from active connection."""
        try:
            buf = self.his_protokol.read(size)
            if isinstance(buf, (bytes, bytearray)):
                self.logger.debug("Received %d bytes: %s", len(buf), _bytes_hex(buf))
            else:
                self.logger.debug("Received object of type %s", type(buf).__name__)
            return buf
        except Exception:
            self.logger.error("Error while receiving data.", exc_info=True)
            raise
    
    def _data_response(self, command, name:str = '') -> bytearray:
        """
        Reads and interprets the response from the device after sending a command.

        Args:
            CommandType: The command byte value that was sent (e.g., GET_MODEL, BUTTON_PRESS).
            name (str): Optional name for logging purposes to indicate which command is being processed.

        Returns:
            Tuple[bool, Optional[int]]: A tuple where the first element indicates success (True/False),
            and the second element contains relevant response data or None.
        """
        # --- Read response ---
        try:
            response = self.his_protokol.read(timeout=1.0)  # adjust timeout as needed
            if not response or not response[0]:
                self.logger.warning("No response received for %s", name)
                return False,None if command != CommandType.GET_MODEL.value else None

            first_byte = response[0][0]
            if first_byte == command:
                if command == CommandType.GET_MODEL.value:
                    self.logger.info("GET_MODEL response: %s", _bytes_hex(response))
                    return  True,response[0][1]
                else:
                    self.logger.info("Press ACK received %s: %s", name, _bytes_hex(response))
                    return True,response[0][0] 
            else:
                self.logger.warning("Unexpected press response %s: %s", name, _bytes_hex(response))
                return False, None

        except Exception:
            self.logger.error("No response after press.", exc_info=True)
            return False, None

    def _send_with_retry(self, command: bytearray, cmd_name: str) -> None:
        """
        Send a command with retry until data_response returns True or max retries reached.
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self.logger.debug("%s (hex): %s", cmd_name, _bytes_hex(command))
                self.his_protokol.write([command])
                sleep(SLEEP_AFTER_CMD)
                data_response = self._data_response(command[0], cmd_name)
                if data_response[0]:
                    self.logger.info("%s ACK received on attempt %d", cmd_name, attempt)
                    return  data_response[1]
                else:
                    self.logger.warning("%s no ACK on attempt %d, resetting connection...", cmd_name, attempt)
                    self.his_protokol.close()
                    sleep(1)
                    self.his_protokol.open()
                    sleep(SLEEP_AFTER_CMD)

            except Exception as e:
                self.logger.error("%s error on attempt %d: %s. Resetting connection...", cmd_name, attempt, e, exc_info=True)
                self.his_protokol.close()
                sleep(1)
                self.his_protokol.open()
                sleep(SLEEP_AFTER_CMD)

        # If we reach here, all attempts failed
        raise RuntimeError(f"{cmd_name} failed after {MAX_RETRIES} attempts")
    
    def _point_to_xy(self, point: Sequence[int]) -> Tuple[int, int]:
        """
        Convert a 2-element sequence into an (x, y) tuple of integers.

        Parameters:
            point (Sequence[int]): A list or tuple containing exactly two integers.

        Returns:
            Tuple[int, int]: A tuple containing (x, y) coordinates.

        Raises:
            ValueError: If the input is not a 2-element sequence of integers.
        """
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(f"Point must be a 2-element sequence, got: {point}")
        x, y = point
        if not (isinstance(x, int) and isinstance(y, int)):
            raise ValueError(f"Coordinates must be integers, got: {point}")
        return x, y

    def button(self, index: int = 0) -> None:
        """
        Simulates a button press on the device by sending press and release commands
        over the protocol connection. Supports short and long presses, repeating presses,
        and automatic recovery if the connection fails.

        Args:
            index (int): The button index to press (default: 0).
            repeat (int): Number of times to repeat the press/release sequence (default: 1).
            hold (float): Duration in seconds to determine press type.
                        If hold < 3 seconds → treated as a normal press.

        """
        #press_type = (
        #    PressType.PRESSED.value if hold < 3
        #    else PressType.LONG_PRESS.value
        #)
        command_press = bytearray([CommandType.BUTTON_PRESS.value]) + bytearray(CommandButton(index, PressType.PRESSED.value))
        #command_released = bytearray([CommandType.BUTTON_PRESS.value]) + bytearray(CommandButton(index, PressType.RELEASED.value))
        try:
            self._send_with_retry(command_press, "Button press")
            sleep(0.2)
        except Exception as e:
            self.logger.warning("[button] Error on attempt %d/%d: %s. Resetting connection...",
                            e, exc_info=True)
            try:
                self.his_protokol.close()
                self.his_protokol.open()
                self.logger.info("Connection reset after button error.")
            except Exception:
                self.logger.error("Failed to reset connection after button error.", exc_info=True)
                raise 

    def touchPress(self, press: Sequence[int]) -> None:
        """
        Simulates a touch press action on the device at the specified coordinates.
        Sends press and release commands, supports short/long press types,
        multiple repeats, and automatically attempts connection recovery on failure.

        Args:
            press (Sequence[int]): The (x, y) coordinates of the touch press.
            repeat (int): Number of times to repeat the press/release sequence (default: 1).
            hold (float): Determines press type.
                        If hold < 3 seconds → short press.
                        If hold >= 3 seconds → long press.
        """
        sx, sy = self._point_to_xy(press)
        command_press =bytearray([CommandType.TOUCH_ACTION.value]) + bytearray(CommandTouch(sx, sy, PressType.PRESSED.value))
        command_released = bytearray([CommandType.TOUCH_ACTION.value]) + bytearray(CommandTouch(sx, sy, PressType.RELEASED.value))
        try:
            self._send_with_retry(command_press, "Touch press")
            sleep(0.01)
            self._send_with_retry(command_released, "Touch release")
            sleep(0.01)
            self._send_with_retry(command_released, "Touch release")
        except Exception as e:
            self.logger.warning("[touchPress] Error: %s. Resetting connection...", e, exc_info=True)
            try:
                self.his_protokol.close()
                self.his_protokol.open()
                self.logger.info("Connection reset after touchPress error.")
            except Exception:
                self.logger.error("Failed to reset connection after touchPress error.", exc_info=True)
                raise

    def touchSlide(
        self,
        start: Sequence[int],
        scroll_rotate: bool = True,     # True = +smer (dol/desno), False = -smer (gor/levo)
        scroll_direction: str = True,  # True = vertikalni Y, False = horizontalni X
        speed: str = "normal"
    ) -> None:
        """
        Simulates a sliding gesture from the given start coordinate.
        Sends PRESS -> one or more MOVED events -> RELEASE at final position.

        Args:
            start (Sequence[int]): Starting (x, y) coordinates of the slide.
            scroll_direction (bool): True => move along Y (vertical); False => move along X (horizontal).
            scroll_rotate (bool): True => positive direction (down/right); False => negative (up/left).
            speed (str): One of {"slow", "normal", "fast"} controlling distance/step/delay.
        """

        # --- speed configuration ---
        # distance: total displacement (px)
        # step: increment per MOVED (px)
        # delay: pause between MOVED events (s)
        SPEED_CFG = {
            "slow":   {"distance": 12, "step": 0, "delay": 0.10},
            "normal": {"distance": 75, "step": 8, "delay": 0.02},
            "fast":   {"distance": 100, "step": 20, "delay": 0.00},
        }
        def _clamp_u16(v: int) -> int:
            return 0 if v < 0 else (65535 if v > 65535 else v)

        def _send_touch(x: int, y: int, press_type, label: str):
            val = press_type.value if hasattr(press_type, "value") else int(press_type)
            payload = CommandTouch(_clamp_u16(int(x)), _clamp_u16(int(y)), val)
            prefix = bytearray([CommandType.TOUCH_ACTION.value])
            self._send_with_retry(prefix + bytearray(payload), label)
        
        try:
            x0, y0 = self._point_to_xy(start)

            cfg = SPEED_CFG.get(speed, SPEED_CFG["normal"])
            step_mag = int(cfg["step"])
            distance_mag = int(cfg["distance"])
            delay = float(cfg["delay"])

            sign = 1 if scroll_rotate else -1
            step = sign * step_mag
            distance = sign * distance_mag

            vertical = bool(scroll_direction)  # True => Y, False => X
            axis_label = "Y" if vertical else "X"

            # PRESS na začetni točki (vedno na (x0, y0))
            _send_touch(x0, y0, PressType.PRESSED, f"Touch slide start press ({axis_label})")
            #print(f"start press at x0={x0}, y0={y0}")
            if vertical:
                # Premik po Y; X ostane x0
                final_main = y0 + distance

                # Začnemo pri prvem koraku od y0
                cur = y0 + step
                # Če je razdalja manjša od enega koraka, prvi premik naj bo kar na final
                if (step > 0 and cur > final_main) or (step < 0 and cur < final_main):
                    cur = final_main

                # Vmesni premiki
                while (step > 0 and cur < final_main) or (step < 0 and cur > final_main):
                    #print(f"cur={cur}, final_main={final_main}, step={step}")
                    _send_touch(x0, cur, PressType.MOVED, f"Touch slide move ({axis_label})")
                    if delay:
                        sleep(delay)
                    cur += step
                ## Zadnji premik na final in RELEASE
                if speed != "fast":
                    #print(f"final move x0={x0}, final_main={final_main}")
                    _send_touch(x0, final_main, PressType.MOVED, f"Touch slide final move ({axis_label})")
                    if delay:
                        sleep(delay)
                _send_touch(x0, final_main, PressType.RELEASED, f"Touch slide end release ({axis_label})")
                #print(f"end release at x0={x0}, final_main={final_main}")
            else:
                # Premik po X; Y ostane y0
                final_main = x0 + distance

                # Začnemo pri prvem koraku od x0
                cur = x0 + step
                # Če je razdalja manjša od enega koraka, prvi premik naj bo kar na final
                if (step > 0 and cur > final_main) or (step < 0 and cur < final_main):
                    cur = final_main
                # Vmesni premiki
                while (step > 0 and cur < final_main) or (step < 0 and cur > final_main):
                    _send_touch(cur, y0, PressType.MOVED, f"Touch slide move ({axis_label})")
                    if delay:
                        sleep(delay)
                    cur += step
                # Zadnji premik na final in RELEASE
                if speed != "fast":
                    _send_touch(final_main, y0, PressType.MOVED, f"Touch slide final move ({axis_label})")
                    if delay:
                        sleep(delay)
                _send_touch(final_main, y0, PressType.RELEASED, f"Touch slide end release ({axis_label})")

        except Exception as e:
            self.logger.warning("[touchSlideNew] Error: %s. Resetting connection...", e, exc_info=True)
            try:
                self.his_protokol.close()
                self.his_protokol.open()
                self.logger.info("Connection reset after touchSlideNew error.")
            except Exception:
                self.logger.error("Failed to reset connection after touchSlideNew error.", exc_info=True)
                raise

    def setLanguages(self, index: int):
        """
        Sends a command to set the device language by index.

        Args:
            index (int): The language index to set. This should correspond to
                        a valid language entry in the device's supported list.
        """
        command = bytearray([CommandType.SET_LANGUAGE.value]) + bytearray(Command(index))
        try:
            self._send_with_retry(command, "Set language")
            sleep(0.2)
        except Exception:
            self.logger.error("Failed to send setLanguages command.", exc_info=True)
            raise

    def setModel(self, model: int):
        """
        Sends a command to set the device model by index.

        Args:
            model (int): The model index to configure. Must correspond to a valid
                        model supported by the device.
        """
        command = bytearray([CommandType.SET_MODEL.value]) + bytearray(CommandModel(model))
        try:
            self._send_with_retry(command, "Set model")
            sleep(0.2)
        except Exception:
            self.logger.error("Failed to send setModel command.", exc_info=True)
            raise

    def getModel(self):
        """
        Sends a command to retrieve the current device model.

        Returns:
            The response from the device, typically containing the current model index or information.

        Note:
            There is a commented test version of the command that appends a fixed value (7) for testing purposes.
        """
        #command = bytearray([CommandType.GET_MODEL.value])+bytearray([7]) # for test
        command = bytearray([CommandType.GET_MODEL.value]) #  
        try:
            return self._send_with_retry(command, "Get model")
        except Exception:
            self.logger.error("Failed to send Get model command.", exc_info=True)
            raise

if __name__ == "__main__":
    dev = DeviceConnection(method="wifi", host="192.168.88.30", port=9005)
    dev.connect()
    try:
        dev.touchPress(100, 200)
        dev.button(index=1, repeat=2, hold=0.1)
        dev.touchSlide((50, 50), (200, 200), time=0.3)
        dev.setModel(4)
        dev.setLanguages(1)
    finally:
        dev.disconnect()

