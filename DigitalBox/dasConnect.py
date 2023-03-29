################################## IMPORTS #######################################
from time import sleep, time
import serial
import traceback
import socket
SEND_TIME = 0.1
PORT = 9001             #ESP32 Server Port   
########################## COMMAND FOR BOX WITH ESP 32 ###########################
MAIN = "SET_MAIN"
DIGITAL_IN = "READ_IN_DATA"
DIGITAL_OUT = "SET_RELAY"
SET_DIGITAL_POT = 'SET_POT'
SET_PWM_1 = "SET_PWM1"
SET_PWM_2 ="SET_PWM2"
READ_PWM = "READ_PWM"
SET_VOLTAGE = "SET_VOLT"
READ_ADC = "READ_ADC"
READ_ADC_WIFI = "WiFi_ADC"
READ_PWM_WIFI = "WiFi_PWM"
################## COMMAND FOR BOX WITH ARDUINO MEGA #############################
SET_DAC = "SET_TEMP"
SET_DUTY = "SET_DC_PWM2kHz"
SET_FREQUENCY = "SET_SIG_f"
##################################################################################
CHECK_VERSION = 'VERZIJa'
errorNumber ='#'*100
analogOutDict = {
        0: "13,A",
        1: "12,D",
        2: "13,B",
        3: "12,C",
        4: "13,C",
        5: "12,B",
        6: "13,D",
        7: "12,A",
    }

def Convert(string):
    list1=[]
    list1[:0]=string
    return list1

def convert_digital_in(read_digital_in):

    all_digital_in =[]
    if read_digital_in.split(' ')[3] == "":
        read_digital_in=read_digital_in + '0'
        #print('ok')
    for index in range(4):
        value = int(read_digital_in.split(' ', 4)[index])
        decimal = bin(value).replace('0b','')
        reverse = decimal[::-1]
        while len(reverse) < 8:
            reverse += '0'
        all_digital_in.extend([bool(int(item)) for item in Convert(reverse[::-1])])
    #print(all_digital_in)
    return all_digital_in

class SERIALCONNECT():
    """
    Connect to digital box:
    example:
    box = SERIALCONNECT('COM19')
    box.connect()
    box.main = 1
    box.disconnect()
    """
    def __init__(self,comport):
        ############################# BEGIN PARAMETERS ##################################
        self.comport = comport
        self._main = 0
        self._digital_in = []
        self._digital_out = [0,0,0,0,0,0,0,0]
        self.digital_out_value = [0,0,0,0,0,0,0,0]
        self.LIST_POT_VALUE =[0,0,0,0,0,0]
        self.LIST_DAC_VALUE =[32768,32768,32768,32768,32768,32768,32768,32768]
        self._set_pwm1 = 0
        self._set_pwm2 = 0
        self._digital_pot = []
        self._analog_out = []
        self._read_pwm = [0,0]
        self._set_dac = 0
        self._set_duty_cycle_out = 0
        self._frequency_out = 0
        self._set_voltage = 0
        self._read_adc = [0,0,0,0]
    
    def connect(self):
        """
        - set baudrate serial communication
        - when serial is connected check box version
        
        self.ser = socket.socket()
        port = 9001             #ESP32 Server Port   
        self.ser.connect((self.comport, port))
          
        """
        try:
            self.ser = serial.Serial()
            self.ser.baudrate = 115200
            self.ser.port = self.comport
            self.ser.timeout=0.01
            self.ser.setDTR(False)
            self.ser.setRTS(False)
            self.ser.open()
            sleep(3)
            ##################check version #############
            self.ser.write(f'{CHECK_VERSION}'.encode())
            sleep(SEND_TIME)
            VERSION = self.ser.readline().decode().strip()
        except:
            print('Device disconnected')
            with open('check_error.txt', 'w') as f:
                f.write(f'{errorNumber}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber}\n')
            f.close()
            self.ser.close()
        return VERSION
        
    
    def disconnect(self):
        """
        close serial connection
        """
        self.ser.close()
    ######################### main on/off #########################
    @property
    def main(self):
        return self._main
    @main.setter
    def main(self,value):
        """
        - set main value
        - self.box.main = 0 / 1
        """
        self.ser.write(f'{MAIN},{value}'.encode())
        self._main = value
        sleep(SEND_TIME)
    @main.getter
    def main(self):
        """
        - get main value 
        - self.box.main
        """
        return self._main
    ########################## digital_in #########################
    @property
    def digital_in(self):
        return self._digital_in
    
    @digital_in.getter
    def digital_in(self):
        """
        -get digital in
        - self.box.digital_in[:] # get all digital in 
        - self.box.digital[0,1,2] # get digital in (0,1,2)
        - return type bool
        """
        self.ser.write(f'{DIGITAL_IN}'.encode())
        sleep(SEND_TIME)
        return convert_digital_in(self.ser.readline().decode())
    ########################## digital_out #########################
    @property

    def digital_out(self):
        return self._digital_out

    #@digital_out.setter
    def set_digital_out(self,*parameters):
        """
        - number type int or tuple
        - value type int
        - self.box.set_digital_out(number,value)
        - self.box.set_digital_out(0,1) set first output to True
        - self.box.set_digital_out([0,1,2],0) set output(0,1,2) to False
        """
        number,value = parameters
        if isinstance(number,tuple):
            for index in number:
                self.digital_out_value[index] = int(value)
        else:
            self.digital_out_value[number] = int(value)
        convertInt = ''.join(map(str, self.digital_out_value))
        digital_out_number = int(convertInt,2)
        self.ser.write(f'{DIGITAL_OUT},{digital_out_number}'.encode())
        self._digital_out = list(map(bool,self.digital_out_value))
        sleep(SEND_TIME)
        
    @digital_out.getter
    def digital_out(self):
        """
        get digital_out
        print(self.box.digital_out)
        return bool
        """
        return self._digital_out
       
    ######################### Digital potentiometer ########################
    @property
    def digital_pot(self):
        return self._digital_pot
    #@digital_pot.setter
    def set_digital_pot(self,chip_output_list,chip_value = 10):
        """_summary_

        Args:
            chip_output_list (_type_): _description_
            chip_value (int, optional): _description_. Defaults to 10.
         
         
         
        - self.box.set_digital_pot([chip_select,chip_output],value)
        fist list number is chip select = 1
        other list is chip output
        - self.box.set_digital_pot([1,0,1],45) on first chip in chip number 0 and 1 set value 45
        """
        self.LIST_POT_VALUE.insert(0,chip_output_list[0])
        for chip_output in chip_output_list[1:]:
            self.ser.write(f'{SET_DIGITAL_POT},{chip_output_list[0]},{chip_output},{chip_value}'.encode())
            sleep(SEND_TIME)
            self.LIST_POT_VALUE[chip_output+1]= chip_value
        self._digital_pot = self.LIST_POT_VALUE
    @digital_pot.getter
    def digital_pot(self):
        return self._digital_pot
    ############################### SET_PWM_1 #############################
    @property
    def set_pwm1(self):
        return self._set_pwm1
    @set_pwm1.setter
    def set_pwm1(self,parameters):
        """
        - self.box.set_pwm1 = (1000,20) set freq(1000) and duty(20)
        first argument is frequency
        second argument is duty
        """
        frequency,duty = parameters
        self.ser.write(f'{SET_PWM_1},{frequency},{duty}'.encode())
        self._set_pwm1 = [frequency,duty]
        sleep(SEND_TIME)
    @set_pwm1.getter
    def set_pwm1(self):
        """get pwm1
        
        print(self.box.set_pwm1)
        """
        return self._set_pwm1
    ############################### SET_PWM_2 #############################
    @property
    def set_pwm2(self):
        return self._set_pwm2
    @set_pwm2.setter
    def set_pwm2(self,parameters):
        """
        - self.box.set_pwm2 = (1000,20) set freq(1000) and duty(20)
        first argument is frequency
        second argument is duty
        """
        frequency,duty = parameters
        self.ser.write(f'{SET_PWM_2},{frequency},{duty}'.encode())
        self._set_pwm2 = [frequency,duty]
        sleep(SEND_TIME)
    @set_pwm2.getter
    def set_pwm2(self):
        """
        get pwm2
        print(self.box.set_pwm2)
        """
        return self._set_pwm2
     ############################### READ_PWM #############################
    @property
    def read_pwm(self):
        return self._read_pwm
    
    @read_pwm.getter
    def read_pwm(self):
        """
        read pwm
        - self.box.read_pwm  - read pwm1 and pwm2
        return
        type dict
        [{"d":d1,"f":f1,},{"d":d2,"f":f2}]
        example:
        read_pwm_all[0]['f'] get frequency form pmw 1
       
        read_pwm_all[1]['d'] get duty form pwm 2
        """
        self.ser.write(f'{READ_PWM},1'.encode())
        sleep(SEND_TIME*2)
        f1 = self.ser.readline().decode().strip()
        d1 = self.ser.readline().decode().strip()
        self.ser.write(f'{READ_PWM},2'.encode())
        sleep(SEND_TIME*2)
        f2 = self.ser.readline().decode().strip()
        d2 = self.ser.readline().decode().strip()
        readPwm1 = {"d":d1,"f":f1,}
        readPwm2 = {"d":d2,"f":f2,}
        self._read_pwm = [readPwm1,readPwm2]
        return self._read_pwm
    ############################### SET_DAC #############################
    @property
    def analog_out(self):
        return self._analog_out
    #@analog_out.setter
    def set_analog_out(self,dac_number,chip_value = 10):
        """
        dac_number = int number(0-7) or tuple (0,1,2)
        value  = int value (0-65535) 
        self.box.set_analog_out(dac_number,value)
        example:
        self.box.set_analog_out(0,40000) set first analog output to value 40000
        self.box.set_analog_out((0,2,3),1000) set analog output(0,2,3) to value 1000
        """
        tempList = []
        if type(dac_number) == int:
            setAnalog = analogOutDict[dac_number]
            self.ser.write(f'{SET_DAC},{setAnalog},{chip_value}'.encode())
            #print(f'{SET_DAC},{setAnalog},{chip_value}',t1-t0)
            self.LIST_DAC_VALUE[dac_number]= chip_value
        if type(dac_number) == tuple:
            for number in dac_number:
                tempList.append(analogOutDict[number])
                tempList.append(chip_value)
                self.LIST_DAC_VALUE[number]= chip_value
            listToStr = ','.join(map(str, tempList))
            self.ser.write(f'{SET_DAC},{listToStr}'.encode())
            self.LIST_DAC_VALUE[number]= chip_value
        sleep(2)
        self._analog_out = self.LIST_DAC_VALUE
    
    @analog_out.getter
    def analog_out(self):
        """
            get analog output
        print(self.box.analog_out)
        
        """
        return self._analog_out

    ######################### SET_DUTY ####################################
    @property
    def duty_cycle_out(self):
        return self._duty_cycle_out
    @duty_cycle_out.setter
    def duty_cycle_out(self,value):
        """
        self.box.duty_cycle_out = 20 - set duty to 20%
        """
        self.ser.write(f'{SET_DUTY},{value}'.encode())
        self._duty_cycle_out = value
        sleep(SEND_TIME)
    @duty_cycle_out.getter
    def duty_cycle_out(self):
        """
        get
        print(self.box.duty_cycle_out)
        """
        return self._duty_cycle_out
    
    
    ######################### SET_FREQUENCY ###############################
    @property
    def frequency_out(self):
        return self._frequency_out
    @frequency_out.setter
    def frequency_out(self,frequency):
        """
        self.box.frequency_out = 1500 - set frequency to 1500 Hz
        """
        self.ser.write(f'{SET_FREQUENCY},{frequency}'.encode())
        self._frequency_out = frequency
        sleep(SEND_TIME)
    @frequency_out.getter
    def frequency_out(self):
        """
        get
        print(self.box.frequency_out)
        
        """
        return self._frequency_out
    
    ############################## SET_VOLTAGE ##############################
    @property
    def set_voltage(self):
        return self._set_voltage
    @set_voltage.setter
    def set_voltage(self,parameters):
        """ 
        output type int(0-3)
        value type float(0,5.0)
        
        self.box.set_voltage = (output,value)
        example:
        self.box.set_voltage = (0,4.3) set first voltage out to 4.3 V
        
        """
        output,value = parameters
        self.ser.write(f'{SET_VOLTAGE},{output},{value} '.encode())
        self._set_voltage = [output,value]
        sleep(SEND_TIME)
    @set_voltage.getter
    def set_voltage(self):
        """
        get
        print(self.set_voltage)
        return
        list [value0,value1,value2,value3]
        """
        return self._set_voltage
    ############################## READ_ADC #################################
    @property
    def read_adc(self):
        return self._read_adc
    @read_adc.getter
    def read_adc(self):
        """
        self.box.read_adc -read all ADC(0-3)
        return
        list [adc0,adc1,adc2,adc3]
        example:
        self.box.read_adc[0] get value for first adc input
        return
        list [adc0]
        """
        self.ser.write(f'{READ_ADC}#'.encode())
        sleep(SEND_TIME*3)
        for index in range(4):
            self._read_adc[index] = float(self.ser.readline().decode().strip())
        return self._read_adc

class WifiEsp32Connect():
    """
    Connect to digital box:
    example:
    box = WifiEsp32Connect('192.168.1.15')
    box.connect()
    box.main = 1
    box.disconnect()
    """
    def __init__(self,comport):
        ############################# BEGIN PARAMETERS ##################################
        self.comport = comport
        self._main = 0
        self._digital_in = []
        self._digital_out = [0,0,0,0,0,0,0,0]
        self.digital_out_value = [0,0,0,0,0,0,0,0]
        self.LIST_POT_VALUE =[0,0,0,0,0,0]
        self.LIST_DAC_VALUE =[32768,32768,32768,32768,32768,32768,32768,32768]
        self._set_pwm1 = 0
        self._set_pwm2 = 0
        self._digital_pot = []
        self._analog_out = []
        self._read_pwm = [0,0]
        self._set_dac = 0
        self._set_duty_cycle_out = 0
        self._frequency_out = 0
        self._set_voltage = 0
        self._read_adc = [0,0,0,0]
    
    def connect(self):
        try:
            self.ser = socket.socket() 
            #print(self.comport)
            self.ser.connect((self.comport, PORT))
            sleep(3)
            self.ser.send(f'{CHECK_VERSION}#'.encode())
            sleep(SEND_TIME)
            self.ser.settimeout(4)
            VERSION = self.ser.recv(1024).decode().strip()
        except:
            print('Device disconnected')
            with open('check_error.txt', 'w') as f:
                f.write(f'{errorNumber}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber}\n')
            f.close()
            self.ser.close()
        return VERSION
    
    def disconnect(self):
        self.ser.send(f'STOP#'.encode())
        sleep(SEND_TIME)
        self.ser.close()
    
    ######################### main on/off #########################
    @property
    def main(self):
        return self._main
    @main.setter
    def main(self,value):
        """
        - set main value
        - self.box.main = 0 / 1
        """
        self.ser.send(f'{MAIN},{value}#'.encode())
        self._main = value
        sleep(SEND_TIME)
    @main.getter
    def main(self):
        """
        - get main value 
        - self.box.main
        """
        return self._main
    ########################## digital_in #########################
    @property
    def digital_in(self):
        return self._digital_in
    
    @digital_in.getter
    def digital_in(self):
        """
        -get digital in
        - self.box.digital_in[:] # get all digital in 
        - self.box.digital[0,1,2] # get digital in (0,1,2)
        - return type bool
        """
        self.ser.send(f'{DIGITAL_IN}#'.encode())
        sleep(SEND_TIME*2)
        return convert_digital_in(self.ser.recv(1024).decode())
    ########################## digital_out #########################
    @property

    def digital_out(self):
        return self._digital_out

    #@digital_out.setter
    def set_digital_out(self,*parameters):
        """
        - number type int or tuple
        - value type int
        - self.box.set_digital_out(number,value)
        - self.box.set_digital_out(0,1) set first output to True
        - self.box.set_digital_out([0,1,2],0) set output(0,1,2) to False
        """
        number,value = parameters
        if isinstance(number,tuple):
            for index in number:
                self.digital_out_value[index] = int(value)
        else:
            self.digital_out_value[number] = int(value)
        convertInt = ''.join(map(str, self.digital_out_value))
        digital_out_number = int(convertInt,2)
        self.ser.send(f'{DIGITAL_OUT},{digital_out_number}#'.encode())
        self._digital_out = list(map(bool,self.digital_out_value))
        sleep(SEND_TIME*2)
        
    @digital_out.getter
    def digital_out(self):
        """
        get digital_out
        print(self.box.digital_out)
        return bool
        """
        return self._digital_out
       
    ######################### Digital potentiometer ########################
    @property
    def digital_pot(self):
        return self._digital_pot
    #@digital_pot.setter
    def set_digital_pot(self,chip_output_list,chip_value = 10):
        """_summary_

        Args:
            chip_output_list (_type_): _description_
            chip_value (int, optional): _description_. Defaults to 10.
         
        - self.box.set_digital_pot([chip_select,chip_output],value)
        fist list number is chip select = 1
        other list is chip output
        - self.box.set_digital_pot([1,0,1],45) on first chip in chip number 0 and 1 set value 45
        """
        self.LIST_POT_VALUE.insert(0,chip_output_list[0])
        for chip_output in chip_output_list[1:]:
            self.ser.send(f'{SET_DIGITAL_POT},{chip_output_list[0]},{chip_output},{chip_value}#'.encode())
            sleep(SEND_TIME*2)
            self.LIST_POT_VALUE[chip_output+1]= chip_value
        self._digital_pot = self.LIST_POT_VALUE
    @digital_pot.getter
    def digital_pot(self):
        return self._digital_pot
    ############################### SET_PWM_1 #############################
    @property
    def set_pwm1(self):
        return self._set_pwm1
    @set_pwm1.setter
    def set_pwm1(self,parameters):
        """
        - self.box.set_pwm1 = (1000,20) set freq(1000) and duty(20)
        first argument is frequency
        second argument is duty
        """
        frequency,duty = parameters
        self.ser.send(f'{SET_PWM_1},{frequency},{duty}#'.encode())
        #print(f'{SET_PWM_1},{frequency},{duty}#')
        self._set_pwm1 = [frequency,duty]
        sleep(SEND_TIME)
    @set_pwm1.getter
    def set_pwm1(self):
        """get pwm1
        
        print(self.box.set_pwm1)
        """
        return self._set_pwm1
    ############################### SET_PWM_2 #############################
    @property
    def set_pwm2(self):
        return self._set_pwm2
    @set_pwm2.setter
    def set_pwm2(self,parameters):
        """
        - self.box.set_pwm2 = (1000,20) set freq(1000) and duty(20)
        first argument is frequency
        second argument is duty
        """
        frequency,duty = parameters
        self.ser.send(f'{SET_PWM_2},{frequency},{duty}#'.encode())
        self._set_pwm2 = [frequency,duty]
        #print(f'{SET_PWM_2},{frequency},{duty}#')
        sleep(SEND_TIME)
    @set_pwm2.getter
    def set_pwm2(self):
        """
        get pwm2
        print(self.box.set_pwm2)
        """
        return self._set_pwm2
     ############################### READ_PWM #############################
    @property
    def read_pwm(self):
        return self._read_pwm
    
    @read_pwm.getter
    def read_pwm(self):
        """
        read pwm
        - self.box.read_pwm  - read pwm1 and pwm2
        return
        type dict
        [{"d":d1,"f":f1,},{"d":d2,"f":f2}]
        example:
        read_pwm[0]['f'] get frequency form pmw 1
       
        read_pwm[1]['d'] get duty form pwm 2
        """
        self.ser.send(f'{READ_PWM_WIFI},1#'.encode())
        sleep(SEND_TIME*2)
        read_pwm_duty1 = self.ser.recv(1024).decode().replace("\r","").split(' ')
        self.ser.send(f'{READ_PWM_WIFI},2#'.encode())
        sleep(SEND_TIME*2)
        read_pwm_duty2 = self.ser.recv(1024).decode().replace("\r","").split(' ')
        readPwm1 = {"d":read_pwm_duty1[1],"f":read_pwm_duty1[0],}
        readPwm2 = {"d":read_pwm_duty2[1],"f":read_pwm_duty2[0],}
        self._read_pwm = [readPwm1,readPwm2]
        return self._read_pwm
    ############################### SET_DAC #############################
    @property
    def analog_out(self):
        return self._analog_out
    #@analog_out.setter
    def set_analog_out(self,dac_number,chip_value = 10):
        """
        dac_number = int number(0-7) or tuple (0,1,2)
        value  = int value (0-65535) 
        self.box.set_analog_out(dac_number,value)
        example:
        self.box.set_analog_out(0,40000) set first analog output to value 40000
        self.box.set_analog_out((0,2,3),1000) set analog output(0,2,3) to value 1000
        """
        tempList = []
        if type(dac_number) == int:
            setAnalog = analogOutDict[dac_number]
            self.ser.send(f'{SET_DAC},{setAnalog},{chip_value}#'.encode())
            self.LIST_DAC_VALUE[dac_number]= chip_value
        if type(dac_number) == tuple:
            for number in dac_number:
                tempList.append(analogOutDict[number])
                tempList.append(chip_value)
                self.LIST_DAC_VALUE[number]= chip_value
            listToStr = ','.join(map(str, tempList))
            self.ser.send(f'{SET_DAC},{listToStr}#'.encode())
            self.LIST_DAC_VALUE[number]= chip_value
        sleep(2)
        self._analog_out = self.LIST_DAC_VALUE
    
    @analog_out.getter
    def analog_out(self):
        """
            get analog output
        print(self.box.analog_out)
        
        """
        return self._analog_out

    ######################### SET_DUTY ####################################
    @property
    def duty_cycle_out(self):
        return self._duty_cycle_out
    @duty_cycle_out.setter
    def duty_cycle_out(self,value):
        """
        self.box.duty_cycle_out = 20 - set duty to 20%
        """
        self.ser.send(f'{SET_DUTY},{value}#'.encode())
        self._duty_cycle_out = value
        sleep(SEND_TIME)
    @duty_cycle_out.getter
    def duty_cycle_out(self):
        """
        get
        print(self.box.duty_cycle_out)
        """
        return self._duty_cycle_out
    
    
    ######################### SET_FREQUENCY ###############################
    @property
    def frequency_out(self):
        return self._frequency_out
    @frequency_out.setter
    def frequency_out(self,frequency):
        """
        self.box.frequency_out = 1500 - set frequency to 1500 Hz
        """
        self.ser.send(f'{SET_FREQUENCY},{frequency}#'.encode())
        self._frequency_out = frequency
        sleep(SEND_TIME)
    @frequency_out.getter
    def frequency_out(self):
        """
        get
        print(self.box.frequency_out)
        
        """
        return self._frequency_out
    
    ############################## SET_VOLTAGE ##############################
    @property
    def set_voltage(self):
        return self._set_voltage
    @set_voltage.setter
    def set_voltage(self,parameters):
        """ 
        output type int(0-3)
        value type float(0,5.0)
        
        self.box.set_voltage = (output,value)
        example:
        self.box.set_voltage = (0,4.3) set first voltage out to 4.3 V
        
        """
        output,value = parameters
        self.ser.send(f'{SET_VOLTAGE},{output},{value}#'.encode())
        self._set_voltage = [output,value]
        sleep(SEND_TIME*2)
    @set_voltage.getter
    def set_voltage(self):
        """
        get
        print(self.set_voltage)
        return
        list [value0,value1,value2,value3]
        """
        return self._set_voltage
    ############################## READ_ADC #################################
    @property
    def read_adc(self):
        return self._read_adc
    @read_adc.getter
    def read_adc(self):
        """
        self.box.read_adc -read all ADC(0-3)
        return
        list [adc0,adc1,adc2,adc3]
        example:
        self.box.read_adc[0] get value for first adc input
        return
        list [adc0]
        """
        self.ser.send(f'{READ_ADC_WIFI}#'.encode())
        sleep(SEND_TIME*2)
        self._read_adc= self.ser.recv(1024).decode().split(' ')
        return self._read_adc
   
"""
box = WifiEsp32Connect("192.168.1.116")

#box = SERIALCONNECT("COM33")
box.connect()
sleep(3)
for _ in range(10):
    #box.set_digital_pot([1,0,1],45)
    #sleep(0.2)
    #print(box.digital_in[:])
    #box.main = 0
    #sleep(0.2)
    box.main = 1
    for a in range(3):
        box.set_voltage = (a,3)
        sleep(0.2)
    #print(box.digital_in[:])
    print('adc read', box.read_adc)
    print('pwm read', box.read_pwm)
    #try:
     #   print('pwm read', box.read_adc)
    #except:
     #   print('no data')
      #  continue
box.disconnect()
"""