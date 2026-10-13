from time import perf_counter
from collections import deque
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from DigitalBox.lib import *
from . import state
from .styles import ButtonStyleOff2, ButtonStyleOn2, InputStyleOff, InputStyleOn


class DigitalControlsMixin:
    def check_all_input(self):
        from time import perf_counter
        t0 = perf_counter()

        self.digitalPotIndex = 1

        try:
            t1 = perf_counter()
            self.read_adc()
            print(f"read_adc: {perf_counter() - t1:.3f}s")

        except Exception:
            ...

        try:
            t1 = perf_counter()
            self.read_pwm()
            print(f"read_pwm: {perf_counter() - t1:.3f}s")

        except Exception:
            ...

        t1 = perf_counter()
        self.check_digital_pot()
        self.check_DAC_pot()
        print(f"check_digital_pot: {perf_counter() - t1:.3f}s")

        self.digitalPotIndex = 0

        print(f"TOTAL: {perf_counter() - t0:.3f}s")

    def button_OnOff(self):
        """
        Toggle the main ON/OFF switch state.
        When turned OFF, the G800 device is disconnected; when turned ON
        it is reconnected again.
        """
        self.index_on_off +=1
        if self.index_on_off >=2:
            self.index_on_off = 0
            self.on_off.setIcon(self.iconOff)
            state.deviceG800.boxOffDeviceDisconnected()
        else:
            self.on_off.setIcon(self.iconOn)
            state.deviceG800.boxOnDeviceDisconnect()

    def output0(self):
        """
        Toggle digital output OUT0 (ON/OFF) and update its icon/style.
        """
        self.index_out[0] +=1
        if self.index_out[0] >= 2:
            self.index_out[0] = 0
            self.OUT0.setStyleSheet(ButtonStyleOff2) 
            self.OUT0.setIcon(self.iconSwitchOff)
        else:
            self.OUT0.setStyleSheet(ButtonStyleOn2)
            self.OUT0.setIcon(self.iconSwitchOn)

    def output1(self):
        """
        Toggle digital output OUT1 (ON/OFF) and update its icon/style.
        """
        self.index_out[1] +=1
        if self.index_out[1] >=2:
            self.index_out[1] =0 
            self.OUT1.setStyleSheet(ButtonStyleOff2) 
            self.OUT1.setIcon(self.iconSwitchOff)
        else:
            self.OUT1.setStyleSheet(ButtonStyleOn2)
            self.OUT1.setIcon(self.iconSwitchOn)

    def output2(self):
        """
        Toggle digital output OUT2 (ON/OFF) and update its icon/style.
        """
        self.index_out[2] +=1
        if self.index_out[2] >=2:
            self.index_out[2] =0  
            self.OUT2.setStyleSheet(ButtonStyleOff2)
            self.OUT2.setIcon(self.iconSwitchOff) 
        else:
            self.OUT2.setStyleSheet(ButtonStyleOn2)
            self.OUT2.setIcon(self.iconSwitchOn)

    def output3(self):
        """
        Toggle digital output OUT3 (ON/OFF) and update its icon/style.
        """
        self.index_out[3] +=1
        if self.index_out[3] >=2:
            self.index_out[3] =0  
            self.OUT3.setStyleSheet(ButtonStyleOff2)
            self.OUT3.setIcon(self.iconSwitchOff) 
        else:
            self.OUT3.setStyleSheet(ButtonStyleOn2)
            self.OUT3.setIcon(self.iconSwitchOn)

    def output4(self):
        """
        Toggle digital output OUT4 (ON/OFF) and update its icon/style.
        """
        self.index_out[4] +=1
        if self.index_out[4] >=2:
            self.index_out[4] =0
            self.OUT4.setStyleSheet(ButtonStyleOff2)
            self.OUT4.setIcon(self.iconSwitchOff)
        else:
            self.OUT4.setStyleSheet(ButtonStyleOn2)
            self.OUT4.setIcon(self.iconSwitchOn)

    def output5(self):
        """
        Toggle digital output OUT5 (ON/OFF) and update its icon/style.
        """
        self.index_out[5] +=1
        if self.index_out[5] >=2:
            self.index_out[5] =0  
            self.OUT5.setStyleSheet(ButtonStyleOff2)
            self.OUT5.setIcon(self.iconSwitchOff)
        else:
            self.OUT5.setStyleSheet(ButtonStyleOn2)
            self.OUT5.setIcon(self.iconSwitchOn)

    def output6(self):
        """
        Toggle digital output OUT6 (ON/OFF) and update its icon/style.
        """
        self.index_out[6] +=1
        if self.index_out[6] >=2:
            self.index_out[6] =0
            self.OUT6.setStyleSheet(ButtonStyleOff2)
            self.OUT6.setIcon(self.iconSwitchOff)
        else:
            self.OUT6.setStyleSheet(ButtonStyleOn2)
            self.OUT6.setIcon(self.iconSwitchOn)

    def output7(self):
        """
        Toggle digital output OUT7 (ON/OFF) and update its icon/style.
        """
        self.index_out[7] +=1
        if self.index_out[7] >=2:
            self.index_out[7] =0
            self.OUT7.setStyleSheet(ButtonStyleOff2)
            self.OUT7.setIcon(self.iconSwitchOff)
        else:
            self.OUT7.setStyleSheet(ButtonStyleOn2)
            self.OUT7.setIcon(self.iconSwitchOn)

    def output8(self):
        """
        Toggle digital output OUT8 (ON/OFF) and update its icon/style.
        """
        self.index_out[8] +=1
        if self.index_out[8] >= 2:
            self.index_out[8] = 0
            self.OUT8.setStyleSheet(ButtonStyleOff2) 
            self.OUT8.setIcon(self.iconSwitchOff)
        else:
            self.OUT8.setStyleSheet(ButtonStyleOn2)
            self.OUT8.setIcon(self.iconSwitchOn)

    def output9(self):
        """
        Toggle digital output OUT9 (ON/OFF) and update its icon/style.
        """
        self.index_out[9] +=1
        if self.index_out[9] >=2:
            self.index_out[9] =0 
            self.OUT9.setStyleSheet(ButtonStyleOff2) 
            self.OUT9.setIcon(self.iconSwitchOff)
        else:
            self.OUT9.setStyleSheet(ButtonStyleOn2)
            self.OUT9.setIcon(self.iconSwitchOn)

    def output10(self):
        """
        Toggle digital output OUT10 (ON/OFF) and update its icon/style.
        """
        self.index_out[10] +=1
        if self.index_out[10] >=2:
            self.index_out[10] =0  
            self.OUT10.setStyleSheet(ButtonStyleOff2)
            self.OUT10.setIcon(self.iconSwitchOff) 
        else:
            self.OUT10.setStyleSheet(ButtonStyleOn2)
            self.OUT10.setIcon(self.iconSwitchOn)

    def output11(self):
        """
        Toggle digital output OUT11 (ON/OFF) and update its icon/style.
        """
        self.index_out[11] +=1
        if self.index_out[11] >=2:
            self.index_out[11] = 0  
            self.OUT11.setStyleSheet(ButtonStyleOff2)
            self.OUT11.setIcon(self.iconSwitchOff) 
        else:
            self.OUT11.setStyleSheet(ButtonStyleOn2)
            self.OUT11.setIcon(self.iconSwitchOn)

    def output12(self):
        """
        Toggle digital output OUT12 (ON/OFF) and update its icon/style.
        """
        self.index_out[12] +=1
        if self.index_out[12] >=2:
            self.index_out[12] =0
            self.OUT12.setStyleSheet(ButtonStyleOff2)
            self.OUT12.setIcon(self.iconSwitchOff)
        else:
            self.OUT12.setStyleSheet(ButtonStyleOn2)
            self.OUT12.setIcon(self.iconSwitchOn)

    def output13(self):
        """
        Toggle digital output OUT13 (ON/OFF) and update its icon/style.
        """
        self.index_out[13] +=1
        if self.index_out[13] >=2:
            self.index_out[13] =0  
            self.OUT13.setStyleSheet(ButtonStyleOff2)
            self.OUT13.setIcon(self.iconSwitchOff)
        else:
            self.OUT13.setStyleSheet(ButtonStyleOn2)
            self.OUT13.setIcon(self.iconSwitchOn)

    def output14(self):
        """
        Toggle digital output OUT14 (ON/OFF) and update its icon/style.
        """
        self.index_out[14] +=1
        if self.index_out[14] >=2:
            self.index_out[14] =0
            self.OUT14.setStyleSheet(ButtonStyleOff2)
            self.OUT14.setIcon(self.iconSwitchOff)
        else:
            self.OUT14.setStyleSheet(ButtonStyleOn2)
            self.OUT14.setIcon(self.iconSwitchOn)

    def output15(self):
        """
        Toggle digital output OUT15 (ON/OFF) and update its icon/style.
        """
        self.index_out[15] +=1
        if self.index_out[15] >=2:
            self.index_out[15] =0
            self.OUT15.setStyleSheet(ButtonStyleOff2)
            self.OUT15.setIcon(self.iconSwitchOff)
        else:
            self.OUT15.setStyleSheet(ButtonStyleOn2)
            self.OUT15.setIcon(self.iconSwitchOn)

    def buttonAuto1(self):
        """
        Toggle AUTO button 1 (ON/OFF) and update its style.
        """
        self.index_auto[0] +=1
        if self.index_auto[0] >=2:
            self.index_auto[0] = 0
            self.AUTO1.setStyleSheet(ButtonStyleOff2)
            #self.AUTO1.setIcon(self.iconSwitchOff)
        else:
            self.AUTO1.setStyleSheet(ButtonStyleOn2)

    def buttonAuto2(self):
        """
        Toggle AUTO button 2 (ON/OFF) and update its style.
        """
        self.index_auto[1] +=1
        if self.index_auto[1] >=2:
            self.index_auto[1] = 0
            self.AUTO2.setStyleSheet(ButtonStyleOff2)
            #self.AUTO2.setIcon(self.iconSwitchOff)
        else:
            self.AUTO2.setStyleSheet(ButtonStyleOn2)

    def buttonAuto3(self):
        """
        Toggle AUTO button 3 (ON/OFF) and update its style.
        """
        self.index_auto[2] +=1
        if self.index_auto[2] >=2:
            self.index_auto[2] = 0
            self.AUTO3.setStyleSheet(ButtonStyleOff2)
            #self.AUTO3.setIcon(self.iconSwitchOff)
        else:
            self.AUTO3.setStyleSheet(ButtonStyleOn2)

    def buttonAuto4(self):
        """
        Toggle AUTO button 4 (ON/OFF) and update its style.
        """
        self.index_auto[3] +=1
        if self.index_auto[3] >=2:
            self.index_auto[3] = 0
            self.AUTO4.setStyleSheet(ButtonStyleOff2)
            #self.AUTO4.setIcon(self.iconSwitchOff)
        else:
            self.AUTO4.setStyleSheet(ButtonStyleOn2)

    def check_input(self):
        """
        read digital input from digital box
        """
        
        state.input = self.box.digital_in[:]
        #print('input--->',input)
        return state.input

    def auto_button_parameters_default(self,index):
        """
        Reset the auto-button state machine parameters at the given index
        (signal_on, signal_off, period, current_output, output_start).
        """
        self.signal_on[index] = 0
        self.signal_off[index] = 0
        self.periode[index] = 0
        self.current_output[index] = None
        self.output_start[index] = None

    def check_output(self):
        """
        set all output parameters and on/off button when state change
        """
        begin_parameter = [self.index_on_off,self.index_out[0],self.index_out[1],self.index_out[2],self.index_out[3],self.index_out[4],self.index_out[5],self.index_out[6],self.index_out[7],self.index_out[8],self.index_out[9],self.index_out[10],self.index_out[11],self.index_out[12],self.index_out[13],self.index_out[14],self.index_out[15]]
        begin_parameter_old = [self.index_on_off,self.index_out[0],self.index_out[1],self.index_out[2],self.index_out[3],self.index_out[4],self.index_out[5],self.index_out[6],self.index_out[7]]
        ############### AUTO BUTTON #############################
        if (self.index_auto[0] % 2) == 0:
            self.AUTO1.setStyleSheet(ButtonStyleOff2)
            #self.AUTO1.setIcon(self.iconSwitchOff)
            self.auto_button_parameters_default(0)
        else:
            try:
                if not isinstance(self.param_auto1, (list, tuple)):
                    print("Invalid param_auto1:", self.param_auto1, type(self.param_auto1))
                    return

                if len(self.param_auto1) < 4:
                    print("param_auto1 has invalid length:", self.param_auto1)
                    return

                
                self.auto_button_function(0,int(self.param_auto1[1]),int(self.param_auto1[2]),self.param_auto1[3])
            except TypeError as e: 
                print(f"1 Error occurred while calling auto_button_function. Problems with reading parameters: {e}")
            self.AUTO1.setStyleSheet(ButtonStyleOn2)
            #self.AUTO1.setIcon(self.iconSwitchOn)
        
        if (self.index_auto[1] % 2) == 0:
            self.AUTO2.setStyleSheet(ButtonStyleOff2)
            #self.AUTO2.setIcon(self.iconSwitchOff)
            self.auto_button_parameters_default(1)
        else:
            try:
                if not isinstance(self.param_auto2, (list, tuple)):
                    print("Invalid param_auto2:", self.param_auto2, type(self.param_auto2))
                    return

                if len(self.param_auto2) < 4:
                    print("param_auto2 has invalid length:", self.param_auto2)
                    return

                
                self.auto_button_function(1,int(self.param_auto2[1]),int(self.param_auto2[2]),self.param_auto2[3])
            except TypeError as e: 
                print(f"2 Error occurred while calling auto_button_function. Problems with reading parameters: {e}")
            self.AUTO2.setStyleSheet(ButtonStyleOn2)
            #self.AUTO2.setIcon(self.iconSwitchOn)
        
        if (self.index_auto[2] % 2) == 0:
            self.AUTO3.setStyleSheet(ButtonStyleOff2)
            #self.AUTO3.setIcon(self.iconSwitchOff)
            self.auto_button_parameters_default(2) 
        else:
            try:
                if not isinstance(self.param_auto3, (list, tuple)):
                    print("Invalid param_auto3:", self.param_auto3, type(self.param_auto3))
                    return

                if len(self.param_auto3) < 4:
                    print("param_auto3 has invalid length:", self.param_auto3)
                    return
                self.auto_button_function(2,int(self.param_auto3[1]),int(self.param_auto3[2]),self.param_auto3[3])
            except TypeError as e:
                self.auto_button_function(0,0,0,0)
                print(f"3 Error occurred while calling auto_button_function. Problems with reading parameters: {e}")
            self.AUTO3.setStyleSheet(ButtonStyleOn2)
            #self.AUTO3.setIcon(self.iconSwitchOn)
        
        if (self.index_auto[3] % 2) == 0:
            self.AUTO4.setStyleSheet(ButtonStyleOff2)
            #self.AUTO4.setIcon(self.iconSwitchOff)
            self.auto_button_parameters_default(3)
        else:
            try:
                if not isinstance(self.param_auto4, (list, tuple)):
                    print("Invalid param_auto4:", self.param_auto4, type(self.param_auto4))
                    return

                if len(self.param_auto4) < 4:
                    print("param_auto4 has invalid length:", self.param_auto4)
                    return

                self.auto_button_function(3,int(self.param_auto4[1]),int(self.param_auto4[2]),self.param_auto4[3])
            except TypeError as e:
                self.auto_button_function(0,0,True,0)
                print(f"4 Error occurred while calling auto_button_function. Problems with reading parameters: {e}")
            self.AUTO4.setStyleSheet(ButtonStyleOn2)
            #self.AUTO4.setIcon(self.iconSwitchOn)
        ###################################################
        if begin_parameter != state.change_parameters or self.connectParameters == 1:
            #print(begin_parameter,change_parameters)
            if (self.index_on_off % 2) == 0:
                #self.on_off.setIcon(self.iconOff)
                self.box.main = 0
                state.change_parameters[0]= 0
            else:
                #self.on_off.setIcon(self.iconOn)
                self.box.main = 1
                state.change_parameters[0]= 1
            #try:
            my_deque = deque(begin_parameter[1:])
            print(my_deque)
            # Rotate the deque by 16 positions to the right
            my_deque.rotate(8)
            parameter_true = tuple([i for i, val in enumerate( my_deque) if  val])
            if parameter_true:
                activate_output(self,parameter_true,True)
            
            parameter_false = tuple([i for i, val in enumerate( my_deque) if not val])
            if parameter_false:
                activate_output(self,parameter_false,False)
            for index in range(8,16):
                eval(f'self.OUT{index}.setEnabled(True)')
            """except:
                print('RPI digital input is not implemented works only for 8 input')
                my_deque = deque(begin_parameter_old[1:])
                #my_deque = deque(begin_parameter[1:])
                # Rotate the deque by 16 positions to the right
                my_deque.rotate(8)
                parameter_true = tuple([i for i, val in enumerate( my_deque) if  val])
                if parameter_true:
                    activate_output(self,parameter_true,True)
                
                parameter_false = tuple([i for i, val in enumerate( my_deque) if not val])
                if parameter_false:
                    activate_output(self,parameter_false,False)
                self.OUT8.setEnabled(False)
                for index in range(8,16):
                    eval(f'self.OUT{index}.setEnabled(False)')"""
   
            if (self.index_out[0] % 2) == 0:
                state.change_parameters[1]= 0
                self.OUT0.setStyleSheet(ButtonStyleOff2)
                self.OUT0.setIcon(self.iconSwitchOff) 
            else:
                state.change_parameters[1]= 1
                self.OUT0.setStyleSheet(ButtonStyleOn2)
                self.OUT0.setIcon(self.iconSwitchOn) 
                
            if (self.index_out[1] % 2) == 0:
                state.change_parameters[2]= 0
                self.OUT1.setStyleSheet(ButtonStyleOff2)
                self.OUT1.setIcon(self.iconSwitchOff)
            else:
                state.change_parameters[2]= 1
                self.OUT1.setStyleSheet(ButtonStyleOn2)
                self.OUT1.setIcon(self.iconSwitchOn) 
                
            if (self.index_out[2] % 2) == 0:
                state.change_parameters[3]= 0    
                self.OUT2.setStyleSheet(ButtonStyleOff2)
                self.OUT2.setIcon(self.iconSwitchOff)
            else:
                state.change_parameters[3]= 1
                self.OUT2.setStyleSheet(ButtonStyleOn2)
                self.OUT2.setIcon(self.iconSwitchOn) 
                
            if (self.index_out[3] % 2) == 0:
                state.change_parameters[4]= 0
                self.OUT3.setStyleSheet(ButtonStyleOff2)
                self.OUT3.setIcon(self.iconSwitchOff)
            else:
                state.change_parameters[4]= 1
                self.OUT3.setStyleSheet(ButtonStyleOn2)
                self.OUT3.setIcon(self.iconSwitchOn)
                
            if (self.index_out[4] % 2) == 0:
                state.change_parameters[5]= 0 
                self.OUT4.setStyleSheet(ButtonStyleOff2)
                self.OUT4.setIcon(self.iconSwitchOff)
            else:
                state.change_parameters[5]= 1
                self.OUT4.setStyleSheet(ButtonStyleOn2)
                self.OUT4.setIcon(self.iconSwitchOn)
                
            if (self.index_out[5] % 2) == 0:
                state.change_parameters[6]= 0
                self.OUT5.setStyleSheet(ButtonStyleOff2)
                self.OUT5.setIcon(self.iconSwitchOff)
            else:
                state.change_parameters[6]= 1
                self.OUT5.setStyleSheet(ButtonStyleOn2) 
                self.OUT5.setIcon(self.iconSwitchOn)
                  
            if (self.index_out[6] % 2) == 0:
                state.change_parameters[7]= 0
                self.OUT6.setStyleSheet(ButtonStyleOff2)
                self.OUT6.setIcon(self.iconSwitchOff)
            else: 
                state.change_parameters[7]= 1
                self.OUT6.setStyleSheet(ButtonStyleOn2)
                self.OUT6.setIcon(self.iconSwitchOn)
            
            if (self.index_out[7] % 2) == 0:
                state.change_parameters[8]= 0
                self.OUT7.setStyleSheet(ButtonStyleOff2)
                self.OUT7.setIcon(self.iconSwitchOff) 
            else:
                state.change_parameters[8]= 1
                self.OUT7.setStyleSheet(ButtonStyleOn2)
                self.OUT7.setIcon(self.iconSwitchOn)
            if (self.index_out[8] % 2) == 0:
                state.change_parameters[9]= 0
                self.OUT8.setStyleSheet(ButtonStyleOff2)
                self.OUT8.setIcon(self.iconSwitchOff) 
            else:
                state.change_parameters[9]= 1
                self.OUT8.setStyleSheet(ButtonStyleOn2)
                self.OUT8.setIcon(self.iconSwitchOn)
            
            if (self.index_out[9] % 2) == 0:
                state.change_parameters[10]= 0
                self.OUT9.setStyleSheet(ButtonStyleOff2)
                self.OUT9.setIcon(self.iconSwitchOff) 
            else:
                state.change_parameters[10]= 1
                self.OUT9.setStyleSheet(ButtonStyleOn2)
                self.OUT9.setIcon(self.iconSwitchOn)
            if (self.index_out[10] % 2) == 0:
                state.change_parameters[11]= 0
                self.OUT10.setStyleSheet(ButtonStyleOff2)
                self.OUT10.setIcon(self.iconSwitchOff) 
            else:
                state.change_parameters[11]= 1
                self.OUT10.setStyleSheet(ButtonStyleOn2)
                self.OUT10.setIcon(self.iconSwitchOn)
            
            if (self.index_out[11] % 2) == 0:
                state.change_parameters[12]= 0
                self.OUT11.setStyleSheet(ButtonStyleOff2)
                self.OUT11.setIcon(self.iconSwitchOff) 
            else:
                state.change_parameters[12]= 1
                self.OUT11.setStyleSheet(ButtonStyleOn2)
                self.OUT11.setIcon(self.iconSwitchOn)
            
            if (self.index_out[12] % 2) == 0:
                state.change_parameters[13]= 0
                self.OUT12.setStyleSheet(ButtonStyleOff2)
                self.OUT12.setIcon(self.iconSwitchOff) 
            else:
                state.change_parameters[13]= 1
                self.OUT12.setStyleSheet(ButtonStyleOn2)
                self.OUT12.setIcon(self.iconSwitchOn)
            
            if (self.index_out[13] % 2) == 0:
                state.change_parameters[14]= 0
                self.OUT13.setStyleSheet(ButtonStyleOff2)
                self.OUT13.setIcon(self.iconSwitchOff) 
            else:
                state.change_parameters[14]= 1
                self.OUT13.setStyleSheet(ButtonStyleOn2)
                self.OUT13.setIcon(self.iconSwitchOn)
            if (self.index_out[14] % 2) == 0:
                state.change_parameters[15]= 0
                self.OUT14.setStyleSheet(ButtonStyleOff2)
                self.OUT14.setIcon(self.iconSwitchOff) 
            else:
                state.change_parameters[15]= 1
                self.OUT14.setStyleSheet(ButtonStyleOn2)
                self.OUT14.setIcon(self.iconSwitchOn)
            
            if (self.index_out[15] % 2) == 0:
                state.change_parameters[16]= 0
                self.OUT15.setStyleSheet(ButtonStyleOff2)
                self.OUT15.setIcon(self.iconSwitchOff) 
            else:
                state.change_parameters[16]= 1
                self.OUT15.setStyleSheet(ButtonStyleOn2)
                self.OUT15.setIcon(self.iconSwitchOn)
            self.connectParameters = 0

    def process_signal(self,index, val, state):
        
        if state =='POSITIVE':
            state = True
        elif state == 'NEGATIVE':
            state = False
        # Initialize output start on first True value
        if val:
            self.output_start[index] = 'begin'

        if self.output_start[index] is None:
            # Before start: just invert the state
            return not state

        # Set signals based on val (same for both state True/False)
        self.signal_on[index] = int(val is True)
        self.signal_off[index] = int(val is False)

        # Period transitions
        if self.periode[index] == 2 and self.signal_off[index]:
            self.periode[index] = 3
            self.signal_on[index] = 0
            self.signal_off[index] = 0

        elif self.periode[index] == 3 and self.signal_on[index]:
            self.periode[index] = 0
            self.signal_off[index] = 0

        elif self.signal_on[index] == 0 and self.signal_off[index] == 1 and self.periode[index] == 0:
            self.periode[index] = 1
            self.signal_on[index] = 0
            self.signal_off[index] = 0

        elif self.signal_on[index] == 1 and self.signal_off[index] == 0 and self.periode[index] == 0:
            self.current_output[index] = state
            self.signal_on[index] = 0
            self.signal_off[index] = 0

        elif self.signal_on[index] == 1 and self.periode[index] == 1:
            self.current_output[index] = not state
            self.periode[index] = 2
            self.signal_on[index] = 0
            self.signal_off[index] = 0

        # Fallback output
        return self.current_output[index] if self.current_output[index] is not None else val

    def auto_button_function(self,index,input_number,output_relay,state):
        state_output = self.process_signal(index,self.read_input[input_number],state)
        #print('stanje',index,self.read_input[input_number],state)
        #print('state',state_output)
        if state_output == True:
            self.index_out[output_relay] = 1
        else:
            self.index_out[output_relay] = 0

    def input_state_indicate(self):
        """
        color digital input state
        """
        self.read_input = self.check_input()
        for index in range(state.DigitalInput):
            if self.read_input[index]== True:
                eval(f'self.INPUT_{index}.setStyleSheet(InputStyleOn)')
                state.change_input[index] = True

            elif self.read_input[index]== False:
                eval(f'self.INPUT_{index}.setStyleSheet(InputStyleOff)')
                state.change_input[index] = False
