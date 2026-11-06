import ctypes
import re
import serial.tools.list_ports


def serial_port_name(text):
    """Return the serial port of a combo entry ("COM3 - ...", "/dev/ttyUSB0 - ..."), or None if it is not a serial port."""
    port = str(text or "").split(" - ", 1)[0].strip()
    if re.fullmatch(r"COM\d+", port, re.IGNORECASE) or port.startswith("/dev/"):
        return port
    return None


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

def listConnection():
    """
    Find all serial connection only Arduino Mega(old box) and ESP32(new box) and convert to list
    Convert to list all rpi 192.168.1.10'--->192.168.1.90    
    """
    LIST_CONNECT =[]
    LIST_CONNECT.clear()
    for USB_PORT in serial.tools.list_ports.comports():
        if 'Arduino Mega' in str(USB_PORT):
            LIST_CONNECT.append(f'{USB_PORT.device} - Arduino Mega 2560') 
        elif'CP210x' in str(USB_PORT) :
            LIST_CONNECT.append(f'{USB_PORT.device} - NodeMCU ESP32')
    #LIST_CONNECT.append("")
    #for ip_address in range(10,100,10):
     #   LIST_CONNECT.append(f'RPI - 192.168.88.{ip_address}')
    #for ip_address in range(10,100,10):
    #    LIST_CONNECT.append(f'RPI - 192.168.1.{ip_address}')
    #for ip_address in range(15,100,10):
     #   LIST_CONNECT.append(f'ESP32 - 192.168.88.{ip_address}')
    
    return LIST_CONNECT

def listDeviceConnection():
    """
    Find all serial connection only Arduino Mega(old box) and ESP32(new box) and convert to list
    Convert to list all rpi 192.168.1.10'--->192.168.1.90    
    """
    LIST_CONNECT =[]
    LIST_CONNECT.clear()
    for USB_PORT in serial.tools.list_ports.comports():
        LIST_CONNECT.append(f'{str(USB_PORT)}')
    return LIST_CONNECT
