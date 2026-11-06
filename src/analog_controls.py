import datetime
import traceback
from PyQt6.QtGui import QFont
from DigitalBox.lib import set_DAC, set_digital_pot, tablePotMaxMin, tableValueMaxMin
from . import state
from .styles import InputStyleOn, PotSlicerLabelStyle
from .box_marks import box_mark_name
from .compact_layout import POT_SLIDER_STYLE, compact_inputs_arranged, compact_layout_wanted, pack_inputs
from .helpers import listDigitalPotTable, sliderColor


class AnalogControlsMixin:
    def color_pot_slider(self, index, R, G, B):
        """Background color of an active slider; the compact layout keeps its large groove and handle."""
        slider = getattr(self, f'digital_pot{index}')
        color = f"background-color: rgb({R},{G},{B})"
        if slider.property('compact_slider'):
            slider.setStyleSheet(POT_SLIDER_STYLE + f"QSlider {{ {color}; }}")
        else:
            slider.setStyleSheet(color)

    def digitalPotTable(self,potTable):
        """
        - set min,max and interval for the slider of the given pot table
        """
        for index,TablePot in enumerate(listDigitalPotTable()[:6]):
            try:
                if TablePot == potTable:
                    min,max = tableValueMaxMin(self,TablePot)
                    getattr(self, f'digital_pot{index}').setMinimum(min-10)
                    getattr(self, f'digital_pot{index}').setMaximum(max+10)
                    getattr(self, f'digital_pot{index}').setTickInterval(int((max +(abs(min)))/20))
                    getattr(self, f'PotMax{index}').setText(str(max+10))
                    getattr(self, f'PotMin{index}').setText(str(min-10))
                    if self.pots_active:  # the sliders look inactive until a box is connected
                        getattr(self, f'PotMin{index}').setStyleSheet(PotSlicerLabelStyle)
                        getattr(self, f'PotMax{index}').setStyleSheet(PotSlicerLabelStyle)
                    R,G,B = sliderColor(self,index,min,max)
                    if index not in self._pot_connected:
                        self._pot_connected.add(index)
                        getattr(self, f'digital_pot{index}').valueChanged.connect(getattr(self, f'SetDigitalPot{index}'))
                    if self.pots_active:
                        getattr(self, f'labelDigitalPot{index}').setStyleSheet(InputStyleOn)
                    getattr(self, f'lcdNumber_digital_pot{index}').display(getattr(self, f'digital_pot{index}').value())
                    getattr(self, f'digital_pot{index}').setValue(min+20)
                    if self.pots_active:
                        self.color_pot_slider(index, R, G, B)
            except Exception:
                x = datetime.datetime.now()
                dateAndTime = x.strftime("%c")
                with open('check_error.txt', 'a') as f:
                    f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                    f.write('!!!Table{x.x}.txt change or in table missing pot value or temperature value !!!\n')
                    f.write('Solution:\n')
                    f.write('-- Dont change name!!! Name must be Table1.1,Table1.2--->Table3.1,Table3.2\n')
                    f.write('-- Table must have temperature and pot value\n')
                    f.write(f'{state.errorNumber*2}\n')
                    f.write(traceback.format_exc())
                    f.write(f'{state.errorNumber*2}\n')
                f.close()

    def apply_pot_tables(self):
        """Set the range of every digital pot slider from its table (Table1.1 ... Table3.2)."""
        self.update_digital_pot_visibility()  # remembers the default state of the sliders first
        for table in listDigitalPotTable()[:6]:
            self.digitalPotTable(table)
        self.update_digital_pot_visibility()

    def update_digital_io_visibility(self):
        """When the box marks define INPUT / OUTPUT names only the inputs / outputs with a name are shown
        (all of them while the layout is edited, so they can be named; deleted ones stay hidden)."""
        data = getattr(self, 'box_mark_data', None)
        editing = getattr(self, 'layout_edit', False)
        deleted = getattr(self, 'hidden_controls', set())
        show_all = getattr(self, 'io_show_all', False)  # RESET LAYOUT: all inputs / outputs until marks are selected again
        for section, prefix, count in (('INPUT', 'INPUT_', 32), ('OUTPUT', 'OUT', 16)):
            defined = bool(data) and section in data
            shown_inputs = []
            for index in range(count):
                widget = getattr(self, f'{prefix}{index}')
                named = not defined or editing or show_all or box_mark_name(data, section, index, '') != ''
                if section == 'INPUT' and compact_layout_wanted():  # no room: only the named inputs, never all of them
                    named = editing or (defined and box_mark_name(data, section, index, '') != '')
                visible = named and widget.objectName() not in deleted
                widget.setVisible(visible)
                if visible:
                    shown_inputs.append(index)
            if section == 'INPUT' and compact_inputs_arranged(self):
                pack_inputs(self, list(range(count)) if editing else shown_inputs)

    def update_digital_pot_visibility(self):
        """All digital potentiometers are shown until a box mark is selected; then only the sliders
        with a name in the box marks are shown, next to each other without gaps."""
        self.update_digital_io_visibility()
        prefixes = ('digital_pot', 'PotMin', 'PotMax', 'lcdNumber_digital_pot', 'labelDigitalPot')
        if not hasattr(self, '_pot_base_x'):
            self._pot_base_x = {f'{prefix}{index}': getattr(self, f'{prefix}{index}').x()
                                for prefix in prefixes for index in range(6)}
            self._pot_default_labels = [(getattr(self, f'labelDigitalPot{index}').text(),
                                         QFont(getattr(self, f'labelDigitalPot{index}').font()))
                                        for index in range(6)]
            self._pot_default_state = [{
                'slider': (getattr(self, f'digital_pot{index}').minimum(), getattr(self, f'digital_pot{index}').maximum(),
                           getattr(self, f'digital_pot{index}').tickInterval(), getattr(self, f'digital_pot{index}').value()),
                **{prefix: (getattr(self, f'{prefix}{index}').styleSheet(),
                            getattr(self, f'{prefix}{index}').text() if prefix in ('PotMin', 'PotMax') else None)
                   for prefix in ('digital_pot', 'PotMin', 'PotMax', 'lcdNumber_digital_pot', 'labelDigitalPot')},
                'lcd': getattr(self, f'lcdNumber_digital_pot{index}').value(),
            } for index in range(6)]
        editing = getattr(self, 'layout_edit', False)  # all sliders are shown while the layout is edited
        active = list(range(6)) if self.active_pots is None or editing else self.active_pots
        deleted = getattr(self, 'hidden_controls', set())  # sliders deleted by the user ("digital_pot<index>")
        active = [index for index in active if f'digital_pot{index}' not in deleted]
        for index in range(6):
            slot = active.index(index) if index in active else index
            for prefix in prefixes:
                widget = getattr(self, f'{prefix}{index}')
                widget.move(self._pot_base_x[f'{prefix}{slot}'], widget.y())
        if self.active_pots is None and not editing:
            # box marks do not define the sliders yet: show only those that do not overlap the controls
            # the user has moved
            active = [index for index in active if not self.pot_overlaps_controls(index)]
        for index in range(6):
            for prefix in prefixes:
                getattr(self, f'{prefix}{index}').setVisible(index in active)
        if getattr(self, '_crop_ready', False) and not self.layout_edit:
            self.change_view_area()

    def reset_digital_pot_view(self):
        """Show all digital potentiometers again with their default names (Table1.1, Table1.2, ...)."""
        self.pots_active = False
        self.active_pots = None
        self.update_digital_pot_visibility()
        for index, (text, font) in enumerate(self._pot_default_labels):
            label = getattr(self, f'labelDigitalPot{index}')
            label.setText(text)
            label.setFont(font)
        for index, state_values in enumerate(self._pot_default_state):
            slider = getattr(self, f'digital_pot{index}')
            minimum, maximum, tick, value = state_values['slider']
            slider.blockSignals(True)
            slider.setMinimum(minimum)
            slider.setMaximum(maximum)
            slider.setTickInterval(tick)
            slider.setValue(value)
            slider.blockSignals(False)
            getattr(self, f'lcdNumber_digital_pot{index}').display(state_values['lcd'])
            for prefix in ('digital_pot', 'PotMin', 'PotMax', 'lcdNumber_digital_pot', 'labelDigitalPot'):
                style, text = state_values[prefix]
                widget = getattr(self, f'{prefix}{index}')
                widget.setStyleSheet(style)
                if text is not None:
                    widget.setText(text)
        self.apply_pot_tables()

    def SetDigitalPot0(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table1.1')
            R,G,B = sliderColor(self,0,min,max)
            self.color_pot_slider(0, R, G, B)
            self.lcdNumber_digital_pot0.display(self.digital_pot0.value())
        return self.digital_pot0.value()

    def SetDigitalPot1(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table1.2')
            R,G,B = sliderColor(self,1,min,max)
            self.color_pot_slider(1, R, G, B)
            self.lcdNumber_digital_pot1.display(self.digital_pot1.value())
        return self.digital_pot1.value()

    def SetDigitalPot2(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table2.1')
            R,G,B = sliderColor(self,2,min,max)
            self.color_pot_slider(2, R, G, B)
            self.lcdNumber_digital_pot2.display(self.digital_pot2.value())
        return self.digital_pot2.value()

    def SetDigitalPot3(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table2.2')
            R,G,B = sliderColor(self,3,min,max)
            self.color_pot_slider(3, R, G, B)
            self.lcdNumber_digital_pot3.display(self.digital_pot3.value())
        return self.digital_pot3.value()

    def SetDigitalPot4(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table3.1')
            R,G,B = sliderColor(self,4,min,max)
            self.color_pot_slider(4, R, G, B)
            self.lcdNumber_digital_pot4.display(self.digital_pot4.value())
        return self.digital_pot4.value()

    def SetDigitalPot5(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table3.2')
            R,G,B = sliderColor(self,5,min,max)
            self.color_pot_slider(5, R, G, B)
            self.lcdNumber_digital_pot5.display(self.digital_pot5.value())
        return self.digital_pot5.value()

    def check_digital_pot(self):
        """
        set digital pot value when value change
        """
        
        self.readDigitalPot0 = self.digital_pot0.value()
        self.readDigitalPot1 = self.digital_pot1.value()
        self.readDigitalPot2 = self.digital_pot2.value()
        self.readDigitalPot3 = self.digital_pot3.value()
        self.readDigitalPot4 = self.digital_pot4.value()
        self.readDigitalPot5 = self.digital_pot5.value()
        ###############################digital potentiometer 1 ######################################################
        if state.beginPotValue[0] != self.readDigitalPot0:
            set_digital_pot(self,self.readDigitalPot0,tableIndex = 1,slider =1,chipSelect = 1)
            state.beginPotValue[0] = self.readDigitalPot0
        elif state.beginPotValue[1] != self.readDigitalPot1:
            set_digital_pot(self,self.readDigitalPot1,tableIndex = 1,slider =2,chipSelect = 1)
            state.beginPotValue[1] = self.readDigitalPot1
        ###############################digital potentiometer 2 ######################################################
        elif state.beginPotValue[2] != self.readDigitalPot2:
            set_digital_pot(self,self.readDigitalPot2,tableIndex = 2,slider =1,chipSelect = 2)
            state.beginPotValue[2] = self.readDigitalPot2
        elif state.beginPotValue[3] != self.readDigitalPot3:
            set_digital_pot(self,self.readDigitalPot3,tableIndex = 2,slider =2,chipSelect = 2)
            state.beginPotValue[3] = self.readDigitalPot3
         ###############################digital potentiometer 3 ######################################################
        elif state.beginPotValue[4] != self.readDigitalPot4:
            set_digital_pot(self,self.readDigitalPot4,tableIndex = 3,slider =1,chipSelect = 3)
            state.beginPotValue[4] = self.readDigitalPot4      
        elif state.beginPotValue[5] != self.readDigitalPot5:
            set_digital_pot(self,self.readDigitalPot5,tableIndex = 3,slider =2,chipSelect = 3)
            state.beginPotValue[5] = self.readDigitalPot5

    def read_adc(self):
        """
        read adc value and show on display
        """
        self.read_adc_all = self.box.read_adc[0:4]
        #print(self.read_adc_all)
        self.readADC0.display(float(self.read_adc_all[0]))
        self.readADC1.display(float(self.read_adc_all[1]))
        self.readADC2.display(float(self.read_adc_all[2]))
        self.readADC3.display(float(self.read_adc_all[3]))

    def read_pwm(self):
        """
        read pwm1 and pwm2 and show on the display
        """
        self.read_pwm_all = self.box.read_pwm[:]
        self.ReadPwm1.display(self.read_pwm_all[0]['f'])
        self.ReadDuty1.display(self.read_pwm_all[0]['d'])
        self.ReadPwm2.display(self.read_pwm_all[1]['f'])
        self.ReadDuty2.display(self.read_pwm_all[1]['d'])

    def set_voltage(self):
        """
        set voltage when value change
        """
        self.readVoltage =[self.SetVoltage0.value(),self.SetVoltage1.value(),self.SetVoltage2.value(),self.SetVoltage3.value()]
        if state.beginSetVoltage[0] != self.readVoltage[0]:
            self.box.set_voltage = (0,self.readVoltage[0])
            state.beginSetVoltage[0] = self.readVoltage[0]
        if state.beginSetVoltage[1] != self.readVoltage[1]:
            self.box.set_voltage = (1,self.readVoltage[1])
            state.beginSetVoltage[1] = self.readVoltage[1]
        if state.beginSetVoltage[2] != self.readVoltage[2]:
            self.box.set_voltage = (2,self.readVoltage[2])
            state.beginSetVoltage[2] = self.readVoltage[2]
        if state.beginSetVoltage[3] != self.readVoltage[3]:
            self.box.set_voltage = (3,self.readVoltage[3])
            state.beginSetVoltage[3] = self.readVoltage[3]

    def SetFrequencyBar1(self):
        """
        - set frequency with slider
        - color the slider when value change
        """
       
        self.SetFrequency1.setValue(self.SetPwmBar1.value())
        self.SetPwmBar1.setStyleSheet(f"background-color: rgb({250-int((self.SetPwmBar1.value()/100))},{250-int((self.SetPwmBar1.value()/100))},255)")

    def SetFrequencyBar2(self):
        """
        - set frequency with slider
        - color the slider when value change
        """
        self.SetFrequency2.setValue(self.SetPwmBar2.value())
        self.SetPwmBar2.setStyleSheet(f"background-color: rgb({250-int((self.SetPwmBar2.value()/100))},{250-int((self.SetPwmBar2.value()/100))},255)")

    def set_pwm1(self):
        """
        set PWM1 when value change
        """
        self.BeginValuePwm1=self.setPwmBegin1.value()
        self.EndValuePwm1=self.setPwmEnd1.value()
        self.SetPwmBar1.setMinimum(self.BeginValuePwm1)
        self.SetPwmBar1.setMaximum(self.EndValuePwm1)
        self.readPwm1 =[self.SetFrequency1.value(),self.SetDuty1.value()]
        self.SetPwmBar1.setValue(self.SetFrequency1.value())
        if state.setPwm1[0] != self.readPwm1[0]:
            self.box.set_pwm1 = (self.readPwm1[0],self.readPwm1[1])
            state.setPwm1[0] = self.readPwm1[0]
        if state.setPwm1[1] != self.readPwm1[1]:
            self.box.set_pwm1 = (self.readPwm1[0],self.readPwm1[1])
            state.setPwm1[1] = self.readPwm1[1]

    def set_pwm2(self):
        """
        set PWM2 when value change
        """
        self.BeginValuePwm2=self.setPwmBegin2.value()
        self.EndValuePwm2=self.setPwmEnd2.value()
        self.SetPwmBar2.setMinimum(self.BeginValuePwm2)
        self.SetPwmBar2.setMaximum(self.EndValuePwm2)
        self.readPwm2 =[self.SetFrequency2.value(),self.SetDuty2.value()]
        self.SetPwmBar2.setValue(self.SetFrequency2.value())
        if state.setPwm2[0] != self.readPwm2[0]:
            self.box.set_pwm2 = (self.readPwm2[0],self.readPwm2[1])
            state.setPwm2[0] = self.readPwm2[0]
        if state.setPwm2[1] != self.readPwm2[1]:
            self.box.set_pwm2 = (self.readPwm2[0],self.readPwm2[1])
            state.setPwm2[1] = self.readPwm2[1]

    def set_frequency_and_duty_old(self):
        """
        set frequency and duty value when value change
        """
        self.readPwmOld =[self.SetFrequencyOld.value(),self.SetDutyOld.value()]
       
        if state.setPwmOld[0] != self.readPwmOld[0]:
            self.box.frequency_out = self.readPwmOld[0]
            state.setPwmOld[0] = self.readPwmOld[0]
        
        if state.setPwmOld[1] != self.readPwmOld[1]:
            self.box.duty_cycle_out = self.readPwmOld[1]
            state.setPwmOld[1] = self.readPwmOld[1]

    def check_DAC_pot(self):
        """
        - if value change send dac value
        """
        
        self.readDac0 = state.SetDacValue.dac_pot0.value()
        self.readDac1 = state.SetDacValue.dac_pot1.value()
        self.readDac2 = state.SetDacValue.dac_pot2.value()
        self.readDac3 = state.SetDacValue.dac_pot3.value()
        self.readDac4 = state.SetDacValue.dac_pot4.value()
        self.readDac5 = state.SetDacValue.dac_pot5.value()
        self.readDac6 = state.SetDacValue.dac_pot6.value()
        self.readDac7 = state.SetDacValue.dac_pot7.value()
        ############################### DAC VALUE 1 ######################################################
        if state.beginDacValue[0] != self.readDac0:
            set_DAC(self,self.readDac0,tableIndex = 0,slider =1)
            state.beginDacValue[0] = self.readDac0
        ############################### DAC VALUE 2 ######################################################
        elif state.beginDacValue[1] != self.readDac1:
            set_DAC(self,self.readDac1,tableIndex = 1,slider =2)
            state.beginDacValue[1] = self.readDac1
        ############################### DAC VALUE 3 ######################################################
        elif state.beginDacValue[2] != self.readDac2:
            set_DAC(self,self.readDac2,tableIndex = 2,slider =3)
            state.beginDacValue[2] = self.readDac2
        ############################### DAC VALUE 4 ######################################################
        elif state.beginDacValue[3] != self.readDac3:
            set_DAC(self,self.readDac3,tableIndex = 3,slider =4)
            state.beginDacValue[3] = self.readDac3
         ############################### DAC VALUE 5 ######################################################
        elif state.beginDacValue[4] != self.readDac4:
            set_DAC(self,self.readDac4,tableIndex = 4,slider =5)
            state.beginDacValue[4] = self.readDac4
        ############################### DAC VALUE 6 ######################################################
        elif state.beginDacValue[5] != self.readDac5:
            set_DAC(self,self.readDac5,tableIndex = 5,slider =6)
            state.beginDacValue[5] = self.readDac5
        elif state.beginDacValue[6] != self.readDac6:
            set_DAC(self,self.readDac6,tableIndex = 6,slider =7)
            state.beginDacValue[6] = self.readDac6
        elif state.beginDacValue[7] != self.readDac7:
            set_DAC(self,self.readDac7,tableIndex = 7,slider =8)
            state.beginDacValue[7] = self.readDac7

    def createPotTable(self):
        """
        - if value change send pot value
        
        """
        
        self.DIGITAL_BOX_MAIN.stop()
        try:
            readPot = state.PotTableSet.Pot_value.value()
            TableFirstMin,TableFirstMax = tablePotMaxMin(self,f"{state.PotTableSet.tableSelection()[0:5]}{state.PotTableSet.tableSelection()[5]}.1")
            #print('readPot',readPot)
            #print('table-->',f"{PotTableSet.tableSelection()[0:5]}{PotTableSet.tableSelection()[5]}.1")
            #print('max=',TableFirstMax)
            if state.beginSetPot != readPot:
                if state.PotTableSet.tableSelection()[7] == '1':
                    state.PotTableSet.closeLableError()
                    if readPot <= 255:
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),0],readPot)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),1,2,3],0)
                    elif readPot > 255 and readPot <= 255*2:
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),0],255)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),1],readPot-255)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2,3],0)
                    elif readPot > 255*2 and readPot <= 255*3:
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),0,1],255)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2],readPot-255*2)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],0)
                    elif readPot > 255*3:
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),0,1,2],255)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],readPot-255*3)
                    state.beginSetPot = readPot
                if state.PotTableSet.tableSelection()[7] == '2':
                    self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),4,5],0)
                    if TableFirstMax <= 255:
                        state.PotTableSet.closeLableError()
                        if readPot <= 255:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),1],readPot)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2,3],0)
                        elif readPot > 255 and readPot <= 255*2:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),1],255)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2],readPot-255)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],0)
                        elif readPot > 255*2 and readPot <= 255*3:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),0,1,2],255)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],readPot-255*2)
                    elif TableFirstMax > 255 and TableFirstMax <= 255*2:
                        state.PotTableSet.closeLableError()
                        if readPot <= 255:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2],readPot)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],0)
                        elif readPot > 255 and readPot <= 255*2:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2],255)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],readPot)
                    elif TableFirstMax > 255*2 and TableFirstMax <= 255*3:
                        state.PotTableSet.closeLableError()
                        if readPot <= 255:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],readPot)
                           
                    elif TableFirstMax > 255*3:
                        state.PotTableSet.showLableError(state.PotTableSet.tableSelection()[5])
                    state.beginSetPot = readPot
                #print(self.box.digital_pot[:])
        except ValueError:
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                f.write(f'!!! {state.PotTableSet.tableSelection()[0:5]}{state.PotTableSet.tableSelection()[5]}.1 is empty or not created properly  !!!\n')
                f.write('Solution:\n')
                f.write(f' Check {state.PotTableSet.tableSelection()[0:5]}{state.PotTableSet.tableSelection()[5]}.1 and try again \n')
                f.write(f'{state.errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{state.errorNumber*2}\n')
            f.close()

    def createDacTable(self):
        """
        - if value change set dac value
        """
        
        readDac = state.DacTableCreate.Dac_value.value()
        self.DIGITAL_BOX_MAIN.stop()
        if state.beginDacPot != readDac:
            self.box.set_analog_out(int(state.DacTableCreate.tableSelection())-1,readDac)
            state.beginDacPot = readDac
