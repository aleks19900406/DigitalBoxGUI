from time import sleep, time
import serial
import traceback
SEND_TIME = 0.1

MAIN = "SET_MAIN"
DIGITAL_IN = "READ_IN_DATA"
DIGITAL_OUT = "SET_RELAY"
SET_DIGITAL_POT = 'SET_POT'
SET_PWM_1 = "SET_PWM1"
SET_PWM_2 ="SET_PWM2"
READ_PWM = "READ_PWM"
SET_VOLTAGE = "SET_VOLT"
READ_ADC = "READ_ADC"
################## COMMAND FOR BOX WITH ARDUINO MEGA #############################
SET_DAC = "SET_TEMP"
SET_DUTY = "SET_DC_PWM2kHz"
SET_FREQUENCY = "SET_SIG_f"
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
    #print('!!!!!!',read_digital_in)
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
    def __init__(self,comport):
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
        #print('init####################################################')
    def connect(self):
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
        self.ser.close()

    ########################## box on/off ########################
    @property
    def main(self):
        return self._main
    @main.setter
    def main(self,value):
        #print('set main')
        self.ser.write(f'{MAIN},{value}'.encode())
        self._main = value
        sleep(SEND_TIME)
    @main.getter
    def main(self):
        #print('get main')
        return self._main
    ########################## digital_in #########################
    @property
    def digital_in(self):
        return self._digital_in
    
    @digital_in.getter
    def digital_in(self):
        #print('get digital_in')
        self.ser.write(f'{DIGITAL_IN}'.encode())
        sleep(SEND_TIME)
        return convert_digital_in(self.ser.readline().decode())
    ########################## digital_out #########################
    @property
    def digital_out(self):
        return self._digital_out

    #@digital_out.setter
    def set_digital_out(self,*parameters):
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
        #print('get digital_out')
        return self._digital_out
       
    ######################### Digital potentiometer ########################
    @property
    def digital_pot(self):
        return self._digital_pot
    #@digital_pot.setter
    def set_digital_pot(self,chip_output_list,chip_value = 10):
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
        # call box.set_pwm1=(1000,20)
        frequency,duty = parameters
        self.ser.write(f'{SET_PWM_1},{frequency},{duty}'.encode())
        self._set_pwm1 = [frequency,duty]
        sleep(SEND_TIME)
    @set_pwm1.getter
    def set_pwm1(self):
        return self._set_pwm1
    ############################### SET_PWM_2 #############################
    @property
    def set_pwm2(self):
        return self._set_pwm2
    @set_pwm2.setter
    def set_pwm2(self,parameters):
        frequency,duty = parameters
        self.ser.write(f'{SET_PWM_2},{frequency},{duty}'.encode())
        self._set_pwm2 = [frequency,duty]
        sleep(SEND_TIME)
    @set_pwm2.getter
    def set_pwm2(self):
        return self._set_pwm2
     ############################### READ_PWM #############################
    @property
    def read_pwm(self):
        return self._read_pwm
    
    @read_pwm.getter
    def read_pwm(self):
        self.ser.write(f'{READ_PWM},1'.encode())
        sleep(SEND_TIME)
        f1 = self.ser.readline().decode().strip()
        d1 = self.ser.readline().decode().strip()
        self.ser.write(f'{READ_PWM},2'.encode())
        sleep(SEND_TIME)
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
        tempList = []
        t0 = time()
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
            #print(f'{SET_DAC},{listToStr}')
            self.LIST_DAC_VALUE[number]= chip_value
        sleep(2)
        self._analog_out = self.LIST_DAC_VALUE
        t1 = time()
    
    @analog_out.getter
    def analog_out(self):
        return self._analog_out

    ######################### SET_DUTY ####################################
    @property
    def set_duty_cycle_out(self):
        return self._set_duty_cycle_out
    @set_duty_cycle_out.setter
    def set_duty_cycle_out(self,value):
        self.ser.write(f'{SET_DUTY},{value}'.encode())
        #print(f'{SET_DUTY},{value}')
        self._set_duty_cycle_out = value
        sleep(SEND_TIME)
    @set_duty_cycle_out.getter
    def set_duty_cycle_out(self):
        return self._set_duty_cycle_out
    
    
    ######################### SET_FREQUENCY ###############################
    @property
    def frequency_out(self):
        return self._frequency_out
    @frequency_out.setter
    def frequency_out(self,frequency):
        self.ser.write(f'{SET_FREQUENCY},{frequency}'.encode())
        #print(f'{SET_FREQUENCY},{frequency}')
        self._frequency_out = frequency
        sleep(SEND_TIME)
    @frequency_out.getter
    def frequency_out(self):
        return self._frequency_out
    
    ############################## SET_VOLTAGE ##############################
    @property
    def set_voltage(self):
        return self._set_voltage
    @set_voltage.setter
    def set_voltage(self,parameters):
        output,value = parameters
        self.ser.write(f'{SET_VOLTAGE},{output},{value} '.encode())
        #print(f'{SET_VOLTAGE},{output},{value}')
        self._set_voltage = [output,value]
        sleep(SEND_TIME)
    @set_voltage.getter
    def set_voltage(self):
        return self._set_voltage
    ############################## READ_ADC #################################
    @property
    def read_adc(self):
        return self._read_adc
    @read_adc.getter
    def read_adc(self):
        self.ser.write(f'{READ_ADC}'.encode())
        #sleep(SEND_TIME*2)
        sleep(SEND_TIME)
        for index in range(4):
            self._read_adc[index] = float(self.ser.readline().decode().strip())
            #print(self._read_adc[index])
        return self._read_adc
       
            
"""
box = SERIALCONNECT('COM14')
box.connect()
sleep(3)
counter=0
t0 =time()
box.frequency_out = 200
print(box.read_adc)
#for index in range(8):
 #   box.set_analog_out(index,30000)
t1=time()
print('time:',t1-t0)
#box.set_pwm1=(1000,20)
#for a in range(3):
#box.set_voltage = (2,4.77)
#box.main = 1
#for _ in range(20):
 #   box.read_pwm = 1
  #  print(box.read_pwm)
#print('one',box.read_adc[0])
#print('#########')

box.disconnect()
"""