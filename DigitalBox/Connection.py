from enum import Enum, auto
from time import sleep, time
import ctypes
import os
import json5
from package.tester.py_stream.stream.byte import SerialStream
from package.tester.py_stream.stream.specializations.hisense import (
        ChecksumType,
        DeviceFamily,
        HisenseStrem,
)
CONFIG_FILE = os.path.join("./","config_file")
path_to_json = os.path.abspath(f"{CONFIG_FILE}/G800_configs.json")
with open(path_to_json) as file:
    # Load the JSON data from the file into a Python object
        data = json5.load(file)

icon_command = 0x0100
DEVICE_NUMBER = 1
FRAME_TYPE = 105
FRAME_SUBTYPE = 0
FRAME_HEADER = bytearray([FRAME_TYPE, FRAME_SUBTYPE,FRAME_SUBTYPE])
class CommandButton(ctypes.BigEndianStructure):
    _fields_ =[("address", ctypes.c_uint16),
            ("on_off", ctypes.c_uint8),
            ("index", ctypes.c_uint8),
            ("type", ctypes.c_uint8)]

class CommandIcon(ctypes.BigEndianStructure):
    _fields_ =[("address", ctypes.c_uint16),
            ("index", ctypes.c_uint16)]

class CommandGet(ctypes.BigEndianStructure):
    _fields_ =[("address", ctypes.c_uint16)]

class CommandSet(ctypes.BigEndianStructure):
    _fields_ =[("address", ctypes.c_uint16),
              ("index", ctypes.c_uint8)]

class PressType(Enum):
    """Press types by hold time"""

    SHORT_PRESS = 1  #: No hold
    MEDIUM_PRESS = auto()  #: 1.5s
    LONG_PRESS = auto()  #: 3s
    DOUBLE_CLICK = auto()
    PRESSED = auto()
    RELEASED = auto()

class G800:
    def __init__(self,comport:str,baudrate:str=230400) -> None:
        self.comport = comport
        self.baudrate = baudrate
        SERIAL1_PARAMS = {"device":self.comport}
        self.s1 = SerialStream(SERIAL1_PARAMS,self.baudrate)
        self.h1 = HisenseStrem(self.s1, DeviceFamily.OVEN,ChecksumType.CHECKSUM16)

    def connect(self):
        self.h1.open()

    def disconnect(self):
        self.h1.close()


    def icon(self,index:int =0):
        commands = bytearray(CommandIcon(icon_command,index))
        self.h1.write([(DEVICE_NUMBER,FRAME_HEADER, commands)])
        sleep(0.2)
        try:
            ret =self.h1.read(timeout=self.h1.TIMEOUT)
        except Exception:
            pass
        finally:
            self.h1.clear_exceptions()

    def button(self,index:int=0,repeat:int = 1):
        HisenseStrem.N_TRIES = 1
        #self.h1.discard()
        button_command = data["LUTS"]["SendCommands"]["BtnTrigger"]
        commands = bytearray(CommandButton(int(button_command,  16),1,index,PressType.SHORT_PRESS.value))
        commandsUnlock = bytearray(CommandButton(int(button_command,  16),0,0,PressType.SHORT_PRESS.value))
        for repeatButton in range(repeat):
            try:
                self.h1.write([(DEVICE_NUMBER,FRAME_HEADER, commands)])
                sleep(0.2)
            except Exception:
                self.h1.close()
                self.h1.open()
                print('error')
                continue
        self.h1.write([(DEVICE_NUMBER,FRAME_HEADER, commandsUnlock)])
        sleep(0.2)
        self.h1.close()
        self.h1.open()
    def get_command(self,command:str):
        commands = data["LUTS"]["SendCommands"][command]
        HisenseStrem.N_TRIES = 1
        allCommand = bytearray(CommandGet(int(commands,  16)))
        self.h1.write([(DEVICE_NUMBER,FRAME_HEADER, allCommand)])
        sleep(0.2)
        try:
            ret =self.h1.read()
        except Exception:
            ret = None
        finally:
            self.h1.clear_exceptions()
        if not ret:
            return bytearray(b"")
        else:
            return ret[0][2][3:]


    def set_model(self,model_number:int=0):
        commands = data["LUTS"]["SendCommands"]["GetModel"]
        HisenseStrem.N_TRIES = 1
        allCommand = bytearray(CommandSet(int(commands,  16),model_number))
        self.h1.write([(DEVICE_NUMBER,FRAME_HEADER, allCommand)])
        sleep(0.2)
        try:
            self.h1.read(timeout=self.h1.TIMEOUT)
        except Exception:
            pass
        finally:
            self.h1.close()
            self.h1.open()
