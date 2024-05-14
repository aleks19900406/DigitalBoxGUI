import ctypes
import glob
import os
from enum import Enum, auto
from time import sleep

import json5
from stream.byte import SerialStream
from stream.specializations.hisense import (
        ChecksumType,
        DeviceFamily,
        HisenseStrem,
)

path_to_json = glob.glob("./config_file/*.json")
path_to_json.sort(key=os.path.getmtime)
#print(path_to_json[-1])
with open(path_to_json[-1]) as file:
    # Load the JSON data from the file into a Python object
    data = json5.load(file)

import serial
DEVICE_NUMBER = 1
FRAME_TYPE = 105
FRAME_SUBTYPE = 0
FRAME_HEADER = bytearray([FRAME_TYPE, FRAME_SUBTYPE,FRAME_SUBTYPE])

class Info(ctypes.BigEndianStructure):
        _pack_ = True
        _fields_ = [
            ("model", ctypes.c_uint8),
            ("version", ctypes.c_uint16),
            ("pt1000", ctypes.c_uint16),
            ("RegStates", ctypes.c_uint8),
            ("system", ctypes.c_uint8),
            ("Mn", ctypes.c_uint8),
            ("Mv", ctypes.c_uint16),
            ("On", ctypes.c_uint16),
            ("Pr", ctypes.c_uint16),
            ("Pv", ctypes.c_uint16),
            ("Sp", ctypes.c_uint16),
            ("heater_state", ctypes.c_uint16),
            ("Oc", ctypes.c_uint16),
            ("Cc", ctypes.c_uint16),
            ("Ct", ctypes.c_uint16),
            ("ntc", ctypes.c_uint8),
            ("meat_probe", ctypes.c_uint8),
        ]

class Steam(ctypes.BigEndianStructure):
        _pack_ = True
        _fields_ = [
            ("Steam", ctypes.c_uint8),
            ("Sst", ctypes.c_uint8),
            ("Fst", ctypes.c_uint8),
            ("Sa", ctypes.c_uint8),
            ("St", ctypes.c_uint8),
            ("F", ctypes.c_uint16),
            ("Fc", ctypes.c_uint32),
            ("Yy", ctypes.c_uint16),
            ("Pk", ctypes.c_uint8),
            ("Ps0", ctypes.c_uint8),
            ("Ps1", ctypes.c_uint8),
            ("Ps2", ctypes.c_uint8),
            ("Ps3", ctypes.c_uint8),
            ("PsPk_c", ctypes.c_uint8),
            ("Sdcc", ctypes.c_uint8),
            ("Oc", ctypes.c_uint16),
            ("Rdc", ctypes.c_uint16),
            ("Sdc", ctypes.c_uint16),
        ]

class GetModel(ctypes.BigEndianStructure):
        _pack_ = True
        _fields_ = [
            ("Model", ctypes.c_uint8),
            ("PbVer", ctypes.c_uint16),
            ("PB1", ctypes.c_uint8),
            ("PB2_1", ctypes.c_uint16),
            ("PB2_2", ctypes.c_uint16),
            ("PB3", ctypes.c_uint16),
            ("crc", ctypes.c_uint64),
            ("KLVer", ctypes.c_uint16),
            ("KL1", ctypes.c_uint16),
            ("KL2", ctypes.c_uint8),
            ("RegVer", ctypes.c_uint16),
            ("ESPVer", ctypes.c_uint16),
            ("Esp1", ctypes.c_uint16),
            ("Esp2", ctypes.c_uint8),
       
        ]

class RegCommandParam(ctypes.BigEndianStructure):
    _pack_ = True
    _fields_ =[
        ("address", ctypes.c_uint16),
        ("enable", ctypes.c_uint8),
        ("enable_inv", ctypes.c_uint8),
        ("Sys", ctypes.c_uint8),
        ("Pw", ctypes.c_uint16),
        ("temp", ctypes.c_uint16),
        ("Step", ctypes.c_uint8),
        ("Light", ctypes.c_uint8),
        ("reg_data", ctypes.c_uint8),]

class CommandButton(ctypes.BigEndianStructure):
    _fields_ =[("address", ctypes.c_uint16),
            ("on_off", ctypes.c_uint8),
            ("index", ctypes.c_uint8),
            ("type", ctypes.c_uint8)]

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
        self.esp = serial.Serial(
        port=self.comport,  # Adjust the port name as necessary
        baudrate=self.baudrate,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout= 0.2)
    def connect(self):
        self.h1.open()
    def disconnect(self):
        self.h1.close()

    def connectESP(self):
        if self.esp.isOpen():
            self.esp.close()
        self.esp.open()
    
    def disconnectESP(self):
        self.esp.close()

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
            self.h1.close()
            sleep(0.1)
            self.h1.open()
        if ret is None:
            return bytearray(b"")
        else:
            return ret[0][2][3:]
        
    def get_parameters(self):
        parameters = None
        commands = data["LUTS"]["SendCommands"]['Reg']
        HisenseStrem.N_TRIES = 10
        allCommand = bytearray(CommandGet(int(commands,  16)))
        self.h1.write([(DEVICE_NUMBER,FRAME_HEADER, allCommand)])
        sleep(0.2)
        try:
            ret =self.h1.read()
        except Exception:
            ret = None
        finally:
            self.h1.close()
            self.h1.open()
        try:
            if ret is None:
                allParam = Info.from_buffer_copy( bytearray(b""))     
            else:
                allParam = Info.from_buffer_copy(ret[0][2][3:])
            
            parameters = {'model' : data['LUTS']['Models'][allParam.model],
                        'version':f'{(allParam.version >> 8) & 0xFF}.{allParam.version & 0xFF}',
                        'pt1000': allParam.pt1000/10,
                        'Reg':data['LUTS']['RegStates'][allParam.RegStates],
                        'system':data['LUTS']['Systems'][allParam.system],
                        'Mn' :allParam.Mn,
                        'Mv' :allParam.Mv,
                        'On' :allParam.On,
                        'Pr' :allParam.Pr,
                        'Pv' :allParam.Pv,
                        'Sp' :allParam.Sp,
                        'heater_state' :allParam.heater_state,
                        'Oc' :allParam.Oc,
                        'Cc' :allParam.Cc,
                        'Ct' :allParam.Ct,
                        'Ntc':allParam.ntc,
                        'Probe':allParam.meat_probe}
        except ValueError:
            self.h1.close()
            self.h1.open()
            pass

        return parameters
    
    def get_steam_parameters(self):
        parameters = None
        commands = data["LUTS"]["SendCommands"]['Steam']
        HisenseStrem.N_TRIES = 10
        allCommand = bytearray(CommandGet(int(commands,  16)))
        self.h1.write([(DEVICE_NUMBER,FRAME_HEADER, allCommand)])
        sleep(0.2)
        try:
            ret =self.h1.read()
        except Exception:
            ret = None
        finally:
            self.h1.close()
            self.h1.open()
        try:
            if ret is None:
                steamParam = Steam.from_buffer_copy( bytearray(b""))     
            else:
                steamParam = Steam.from_buffer_copy(ret[0][2][3:])
            
            parameters = {'Steam' : data['LUTS']['SteamStates'][steamParam.Steam],
                        'Sst':data['LUTS']['SteamSubStates'][steamParam.Sst],
                        'Fst': data['LUTS']['FlowSensorStates'][steamParam.Fst],
                        'Sa':data['LUTS']['SteamAssist'][steamParam.Sa],
                        'St':steamParam.St,
                        'F' :f'{steamParam.F}ul',
                        'Fc' :f'{steamParam.Fc}ul',
                        'Yy' :f'{steamParam.Yy}ul',
                        'Pk' :steamParam.Pk,
                        'Ps1' :[steamParam.Ps1],
                        'Ps2' :[steamParam.Ps2],
                        'Ps3' :[steamParam.Ps3],
                        '(Ps<Pk)c' :steamParam.PsPk_c,
                        'Sdcc' :steamParam.Sdcc & 0xf |(-(steamParam.Sdcc & 0x8)),
                        'Oc' :steamParam.Oc,
                        'Rdc' :steamParam.Rdc,
                        'Sdc' :steamParam.Sdc,}
        except ValueError:
            self.h1.close()
            self.h1.open()
            pass
        return parameters

    def startReg(self,enable:int=1,system:int=0,power:int=0,temp:int=0,step:int=0,light:int=1,invalid:int=0,reg:int=1,steam_assist:int=0,steam_fill:int=0,sabbath:int=1,standby:int=0,low_power:int=0):   
        HisenseStrem.N_TRIES = 1
        commands = data["LUTS"]["SendCommands"]['UIRegOVRD']
        reg_data = (invalid | reg << 1 | steam_assist << 2 | steam_fill << 4 | sabbath << 5 | standby << 6 | low_power << 7)
        allCommand =  bytearray(RegCommandParam(int(commands,  16),enable,~enable,system,power,temp,step,light,reg_data))
        self.h1.write([(DEVICE_NUMBER,FRAME_HEADER, allCommand)])
        sleep(0.2)
        try:
            self.h1.read(timeout=self.h1.TIMEOUT)
        except Exception:
            pass
        finally:
            self.h1.close()
            self.h1.open()
    
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

    def get_model(self):
        commands = data["LUTS"]["SendCommands"]["GetModel"]
        HisenseStrem.N_TRIES = 10
        Command = bytearray(CommandGet(int(commands,  16)))
        self.h1.write([(DEVICE_NUMBER,FRAME_HEADER, Command)])
        sleep(0.2)
        #print(DEVICE_NUMBER,FRAME_HEADER, Command)
        try:
            ret =self.h1.read()
        except Exception:
            ret = None
        finally:
            self.h1.close()
            self.h1.open()
        try:
            if ret is None:
                Model = GetModel.from_buffer_copy( bytearray(b""))     
            else:
                Model = GetModel.from_buffer_copy(ret[0][2][3:])
            parameters = {'model' : data['LUTS']['Models'][Model.Model],
                        'PB ver':f'{Model.PbVer}_{Model.PB1}_{Model.PB2_1}.{Model.PB2_2}.{Model.PB3}',
                        'crc' :Model.crc,
                        'KLVer' :f'{(Model.KLVer >> 8) & 0xFF}_{Model.KLVer & 0xFF}_{(Model.KL1 >> 8) & 0xFF}.{Model.KL1 & 0xFF}.{Model.KL2}',
                        'RegVer' :f'{(Model.RegVer >> 8) & 0xFF}.{Model.RegVer & 0xFF}',
                        'ESPVer' :f'{(Model.ESPVer >> 8) & 0xFF}_{Model.ESPVer & 0xFF}_{(Model.Esp1 >> 8) & 0xFF}.{Model.Esp1 & 0xFF}.{Model.Esp2}',}
        except ValueError:
            self.h1.close()
            self.h1.open()
            pass
        return parameters
    
    def button_ESP(self,index,repeat=1,press=1):
        """_summary_

        Args:
            index (_type_): _description_
            repeat (int, optional): _description_. Defaults to 1.
            press (int, optional): _description_. Defaults to 1.
        """
        if int(index) <= 9:
            index = f'0{index}'
        for _ in range(repeat):
            self.esp.write(f"RAW TOUCH {press}{index}\r".encode())
            sleep(0.1)
    def change_language(self,index):
        """_summary_

        Args:
            index (_type_): _description_
        """
        index = "{:02d}".format(index)
        self.esp.write(f"RAW LANG {index}\r".encode())