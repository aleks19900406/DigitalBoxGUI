import glob
from time import sleep
import serial 

def Convert(string):
    list1=[]
    list1[:0]=string
    return list1

def convert_digital_in(read_digital_in):
    all_digital_in =[]
    if read_digital_in.split(' ')[3] == "":
        read_digital_in=read_digital_in + '0'
        print('ok')
    print(read_digital_in)
    for index in range(4):
        value = int(read_digital_in.split(' ', 4)[index])
        decimal = bin(value).replace('0b','')
        reverse = decimal[::-1]
        while len(reverse) < 8:
            reverse += '0'
        all_digital_in.extend([bool(int(item)) for item in Convert(reverse[::-1])])
    return all_digital_in

ser = serial.Serial()
ser.baudrate = 115200
ser.port = 'COM14'
ser.timeout=0.1
ser.setDTR(False)
ser.setRTS(False)
ser.open()
sleep(2)
ser.write('SET_MAIN,1'.encode())
print('begin')
sleep(2)
for _ in range(10):
    ser.write('READ_IN_DATA'.encode())
    convert_digital_in(ser.readline().decode())

ser.close()




"""
import serial.tools.list_ports
for USB_PORT in serial.tools.list_ports.comports():
    if 'Arduino Mega' in str(USB_PORT) or 'CP210x' in str(USB_PORT) :
        print (str(USB_PORT))
""" 
