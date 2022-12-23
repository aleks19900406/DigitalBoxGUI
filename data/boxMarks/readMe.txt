
Full version!
##################################### ALL MARKS #######################
INPUT
PR1,FAN,H_LOW,INFRA,H_UP,,,,PUMP,COOL2,PLOCK,LIGHT,COOL,FAN_OVEN
OUTPUT
out0,out1,out2,out3,,,out6
DIGITAL_POT
PT1000,MEAT,temp3,,temp5
DAC_POT
value0,value1,,value3
READ_ADC
read0,read1,read2,read3
SET_VOLTAGE
read0,adc1,adc2,adc3
READ_PWM1
FREQ1,DUTY1
READ_PWM2
FREQ2,DUTY2
SET_PWM1
SFreq1,SDuty1
SET_PWM2
SFreq2,SDuty2
SET_FREQ
SetFreq(Duty50%)
SET_DUTY
SetDuty(2kHz)
#######################################################################
Instructions:
- Create any file_name.txt  in path ../data/boxMarks
- Select marks which you needed and enter any name you like.
  example:
	INPUT
	PR1,FAN,H_LOW,INFRA,H_UP,,,,PUMP,COOL2,PLOCK,LIGHT,COOL,FAN_OVEN
	OUTPUT
	out0,out1,out2,out3,,,out6
	DIGITAL_POT
	PT1000,MEAT,temp3,,temp5
- You can create more box marks for different test device.




