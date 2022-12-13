from os.path import join 
import os
import operator
import xlrd
from package.tester.helpers.fileio import (
    file_by_tag_and_extension,
    sheet_by_tag,
    tabular_sheet_to_dict,
)

HUSA_USER_INTERFACE = join("data", "husa","user_interface")
BIO21_USER_INTERFACE = join("data", "bio21","digital_box")
POT_TABLE =os.path.join("data",'digitalPotTable')
LOOKUP_TABLE = os.path.join(POT_TABLE,'Table')
DAC_TABLE = os.path.join("data",'dacTable')


def dacValueMaxMin(self,TablePot):
    OPEN_TABLE = open(f'{DAC_TABLE}\\{TablePot}.txt')
    dict_temp = {}
    for line in OPEN_TABLE:
            key,value = line.split()
            #print(value,key)
            dict_temp[float(key)] = value
    
    return [int(min(dict_temp.items(), key=operator.itemgetter(0))[0]),int(max(dict_temp.items(), key=operator.itemgetter(0))[0])]

def set_DAC(self,temp: int,tableIndex,slider = 1):
    OPEN_TABLE = open(f'{DAC_TABLE}\\Table{slider}.txt')
    dict_temp = {}
    for line in OPEN_TABLE:
            key,value  = line.split()
            #print(value,key)
            dict_temp[float(key)] = value
    res = int((dict_temp.get(temp)or dict_temp[min(dict_temp.keys(), key=lambda key: abs(key - temp))])
    )
    print('DAC VALUE',res)
    self.box.set_analog_out(tableIndex,res)


def tableValueMaxMin(self,TablePot):
    OPEN_TABLE = open(f'{POT_TABLE}\\{TablePot}.txt')
    dict_temp = {}
    for line in OPEN_TABLE:
            key,value = line.split()
            #print(value,key)
            dict_temp[float(key)] = value
    
    return [int(min(dict_temp.items(), key=operator.itemgetter(0))[0]),int(max(dict_temp.items(), key=operator.itemgetter(0))[0])]
 
def getMaxTableValue(self,tableIndex,slider):
    OPEN_TABLE = open(f'{LOOKUP_TABLE}{tableIndex}.{slider}.txt')
    dict_temp = {}
    for line in OPEN_TABLE:
            key,value = line.split()
            #print(value,key)
            dict_temp[float(key)] = value
    
    return int(max(dict_temp.items(), key=operator.itemgetter(0))[1])
    
def set_digital_pot(self,temp: int,tableIndex = 1,slider =1,chipSelect = 1):
    OPEN_TABLE = open(f'{LOOKUP_TABLE}{tableIndex}.{slider}.txt')
    dict_temp = {}
    for line in OPEN_TABLE:
            key,value  = line.split()
            #print(value,key)
            dict_temp[float(key)] = value
  
    tableMaxSlider = getMaxTableValue(self,tableIndex,1)

    res = int((dict_temp.get(temp)or dict_temp[min(dict_temp.keys(), key=lambda key: abs(key - temp))])
    )
    print('DIGITAL VALUE',res,tableMaxSlider)
    
    if slider==1:
        #print(f'11111table {tableIndex}.1 chipSelect',chipSelect)
        if tableMaxSlider <= 255:
            if res <= 255:
                self.box.set_digital_pot([chipSelect,0],res)
                #self.box.set_digital_pot([chipSelect,1,2,3],0)
         ############################################################   
        elif (tableMaxSlider > 255 and tableMaxSlider <= 255*2):
            if res <= 255:
                self.box.set_digital_pot([chipSelect,0],res)
                self.box.set_digital_pot([chipSelect,1],0)
            elif res > 255 and res <= 255*2:
                self.box.set_digital_pot([chipSelect,0],255)
                self.box.set_digital_pot([chipSelect,1],res-255)
        #################################################################
        elif (tableMaxSlider > 255*2 and tableMaxSlider <= 255*3):
            if res <= 255:
                self.box.set_digital_pot([chipSelect,0],res)
                self.box.set_digital_pot([chipSelect,1,2],0)
            elif res > 255 and res <= 255*2:
                self.box.set_digital_pot([chipSelect,0],255)
                self.box.set_digital_pot([chipSelect,1],res-255)
                self.box.set_digital_pot([chipSelect,2],0)
            elif res > 255*2 and res <= 255*3:
                self.box.set_digital_pot([chipSelect,0,1],255)
                self.box.set_digital_pot([chipSelect,2],res-255*2)
        
        elif tableMaxSlider > 255*3:
            if res <= 255:
                self.box.set_digital_pot([chipSelect,0],res)
                self.box.set_digital_pot([chipSelect,1,2,3],0)
            elif res > 255 and res <= 255*2:
                self.box.set_digital_pot([chipSelect,0],255)
                self.box.set_digital_pot([chipSelect,1],res-255)
                self.box.set_digital_pot([chipSelect,2],0)
            elif res > 255*2 and res <= 255*3:
                self.box.set_digital_pot([chipSelect,0,1],255)
                self.box.set_digital_pot([chipSelect,2],res-255*2)
                self.box.set_digital_pot([chipSelect,3],0)
            elif res > 255*3:
                self.box.set_digital_pot([chipSelect,0,1,2],255)
                self.box.set_digital_pot([chipSelect,3],res-255*3)
    elif slider == 2:
        #print(f'222table {tableIndex}.2 chipSelect',chipSelect)
        ######################################################
        if res <= 255 and tableMaxSlider <= 255:
            self.box.set_digital_pot([chipSelect,1],res)
            self.box.set_digital_pot([chipSelect,2,3],0)
        elif res > 255 and res <= 255*2 and tableMaxSlider <= 255:
            self.box.set_digital_pot([chipSelect,1],255)
            self.box.set_digital_pot([chipSelect,2],res -255)
            self.box.set_digital_pot([chipSelect,3],0)
        elif res > 255*2 and res <= 255*3 and tableMaxSlider <= 255:
            self.box.set_digital_pot([chipSelect,1,2],255)
            self.box.set_digital_pot([chipSelect,3],res -255*2)  
        elif res > 255*3 and tableMaxSlider <= 255:
            self.box.set_digital_pot([chipSelect,1,2,3],255)
            print(f'Table {tableIndex}.2 is to big > 765 table max slider  {tableIndex}.1 is {tableMaxSlider}')
        #######################################################
        if res <= 255 and (tableMaxSlider > 255 and tableMaxSlider <= 255*2):
            self.box.set_digital_pot([chipSelect,2],res)
            self.box.set_digital_pot([chipSelect,3],0)
        elif (res > 255 and res <= 255*2) and (tableMaxSlider > 255 and tableMaxSlider <= 255*2):
            self.box.set_digital_pot([chipSelect,2],255)
            self.box.set_digital_pot([chipSelect,3],res -255)
        elif res > 255*2 and (tableMaxSlider > 255 and tableMaxSlider <= 255*2):
            self.box.set_digital_pot([chipSelect,2,3],255)
            print(f'Table {tableIndex}.2 is to big > 510 table max slider  {tableIndex}.1 is {tableMaxSlider}')
        #######################################################
        if res <= 255 and (tableMaxSlider > 255*2 and tableMaxSlider <= 255*3):
            self.box.set_digital_pot([chipSelect,3],res)
        elif res > 255 and (tableMaxSlider > 255*2 and tableMaxSlider <= 255*3):
            self.box.set_digital_pot([chipSelect,3],255)
            print(f'Table {tableIndex}.2 is to big > 510 table max slider  {tableIndex}.1 is {tableMaxSlider}')
        ####################################################### 
        if  tableMaxSlider > 255*3:
            print(f'Table {tableIndex}.2 can not be used because table {tableIndex}.1 is to big !!!')
    
    #return  self.box.digital_pot,tableIndex,slider


#### select PB_model and auto select LB model ######
def select_model(self,model_name= 'M1'):
    file_path = file_by_tag_and_extension(
    HUSA_USER_INTERFACE,'IconLedPlus', "xlsx"
    )
    wb = xlrd.open_workbook(file_path)
    Model_PB = wb.sheet_by_index(sheet_by_tag(wb, 'Models_PB'))
    get_all_models_PB = tabular_sheet_to_dict(Model_PB)

    Model_LB = wb.sheet_by_index(sheet_by_tag(wb, 'Models_LB'))
    get_all_models_LB = tabular_sheet_to_dict(Model_LB)
    Model_table = wb.sheet_by_index(sheet_by_tag(wb, 'Models_table'))
    models_table = tabular_sheet_to_dict(Model_table)
    MODELS =[]
    for all_models in get_all_models_PB:
        MODELS.append(get_all_models_PB[all_models]['Model_name'])
        if model_name == get_all_models_PB[all_models]['Model_name']:
            #print('model_name',all_models,get_all_models[all_models]['Model_name'],int(get_all_models[all_models]['DAC_value']))
            reg_model = get_all_models_PB[all_models]['reg_model']
            Model_LB = int(models_table[reg_model]['Models_LB'])
            self.box.set_analog_out(0,int(get_all_models_PB[all_models]['DAC_value']))
            self.box.set_analog_out(1,int(get_all_models_LB[f'M{Model_LB}']['DAC_value']))
            #print('reg model',reg_model,'Model_LB',Model_LB)
           
        elif model_name == all_models: # M0-M9
            #print('model',all_models,get_all_models[all_models]['Model_name'],int(get_all_models[all_models]['DAC_value']))
            reg_model = get_all_models_PB[all_models]['reg_model']
            Model_LB = int(models_table[reg_model]['Models_LB'])
            self.box.set_analog_out(0,int(get_all_models_PB[all_models]['DAC_value']))
            self.box.set_analog_out(1,int(get_all_models_LB[f'M{Model_LB}']['DAC_value']))
            #print('Model_LB_set',int(get_all_models_LB[f'M{Model_LB}']['DAC_value']))
            
    #print(model_name)       
    return model_name,Model_LB
###############GET LB MODEL ########################
def getLBModel(self,model_name= 'M1'):
    file_path = file_by_tag_and_extension(
    HUSA_USER_INTERFACE,'IconLedPlus', "xlsx"
    )
    wb = xlrd.open_workbook(file_path)
    Model_PB = wb.sheet_by_index(sheet_by_tag(wb, 'Models_PB'))
    get_all_models_PB = tabular_sheet_to_dict(Model_PB)

    Model_LB = wb.sheet_by_index(sheet_by_tag(wb, 'Models_LB'))
    get_all_models_LB = tabular_sheet_to_dict(Model_LB)
    Model_table = wb.sheet_by_index(sheet_by_tag(wb, 'Models_table'))
    models_table = tabular_sheet_to_dict(Model_table)
    MODELS =[]
    for all_models in get_all_models_PB:
        MODELS.append(get_all_models_PB[all_models]['Model_name'])
        if model_name == get_all_models_PB[all_models]['Model_name']:
            #print('model_name',all_models,get_all_models[all_models]['Model_name'],int(get_all_models[all_models]['DAC_value']))
            reg_model = get_all_models_PB[all_models]['reg_model']
            Model_LB = int(models_table[reg_model]['Models_LB'])
        elif model_name == all_models: # M0-M9
            #print('model',all_models,get_all_models[all_models]['Model_name'],int(get_all_models[all_models]['DAC_value']))
            reg_model = get_all_models_PB[all_models]['reg_model']
            Model_LB = int(models_table[reg_model]['Models_LB'])
            
    #print(model_name)       
    return Model_LB

############ select_LB_model ######################
def select_model_LB(self,model_name= 'M1'):
    file_path = file_by_tag_and_extension(
    HUSA_USER_INTERFACE,'IconLedPlus', "xlsx"
    )
    wb = xlrd.open_workbook(file_path)
    ws = wb.sheet_by_index(sheet_by_tag(wb, 'Models_LB'))
    get_all_models = tabular_sheet_to_dict(ws)
    MODELS =[]
    for all_models in get_all_models:
        MODELS.append(get_all_models[all_models]['Model_name'])
        if model_name == get_all_models[all_models]['Model_name']:
            #print('model_name',all_models,get_all_models[all_models]['Model_name'],int(get_all_models[all_models]['DAC_value']))
            self.box.set_analog_out(1,int(get_all_models[all_models]['DAC_value']))
        elif model_name == all_models: # M0-M9
            #print('model',all_models,get_all_models[all_models]['Model_name'],int(get_all_models[all_models]['DAC_value']))
            self.box.set_analog_out(1,int(get_all_models[all_models]['DAC_value']))
    #print(model_name,'number', self.box.analog_out[1])       
    return model_name
################## bio21 pyro select_system#################
def select_system(self, program_name):
        file_path = file_by_tag_and_extension(
            BIO21_USER_INTERFACE, "digital_box_in_out", "xlsx"
        )
        wb = xlrd.open_workbook(file_path)
        ws = wb.sheet_by_index(sheet_by_tag(wb, "Pyro_heaters"))
        get_system = tabular_sheet_to_dict(ws)
        
        try:
            DIGITAL_ON = get_system[program_name]["digital_out_ON"].replace(",", "")
            list_digital_on = []
            list_digital_on[:0] = DIGITAL_ON
            for digital_on in list_digital_on:
                self.box.set_digital_out(int(digital_on),1)
                self.index_out[int(digital_on)] = 1
        except KeyError:
            pass
        try:
            DIGITAL_OFF = get_system[program_name]["digital_out_OFF"].replace(",", "")
            list_digital_off = []
            list_digital_off[:0] = DIGITAL_OFF
            for digital_off in list_digital_off:
                self.box.set_digital_out(int(digital_off),0)
                self.index_out[int(digital_off)] = 0
        except KeyError:
            pass
        

