import os
from . import state
from .paths import BOX_DIGITAL_DAC_PATH, BOX_DIGITAL_POT_PATH, BOX_MARKS_PATH, DATA_SAVE


def listDigitalDacTable():
    """
    Convert all DacTable file name to list except readMe.txt
    """
    DigitalDacList =[]
    DigitalDacList.clear()
    for file_name in os.listdir(BOX_DIGITAL_DAC_PATH):
        if file_name == "readMe.txt":
            continue
        if file_name.endswith('.txt'):
            DigitalDacList.append(file_name.replace('.txt',''))
    return DigitalDacList

def dataFile():
    """
    Convert all saveData file name to list but only file with the extension .xlsx
    """
    dataSave =[]
    dataSave.clear()
    #dataSave.append('')
    for file_name in os.listdir(DATA_SAVE):
        if file_name.endswith('.csv'):
            dataSave.append(file_name.replace('.csv',''))
    return dataSave

def listBoxMarks():
    """
    Convert all boxMarks file name to list except readMe.txt
    """
    boxMarkList =[]
    boxMarkList.clear()
    for file_name in os.listdir(BOX_MARKS_PATH):
        #print(file_name)
        if file_name == "readMe.txt":
            continue
        if file_name.endswith('.txt'):
            boxMarkList.append(file_name.replace('.txt',''))
    return boxMarkList

def listDigitalPotTable():
    """
        Convert all digitalPotTable file name to list except readMe.txt
    """
    DigitalPotList =[]
    DigitalPotList.clear()
    for file_name in os.listdir(BOX_DIGITAL_POT_PATH):
        if file_name == "readMe.txt":
            continue
        if file_name.endswith('.txt'):
            DigitalPotList.append(file_name.replace('.txt',''))
    return DigitalPotList

def deliteListDigitalPotTable():
    """
    - refresh file and reload
    """
    DigitalPotList =[]
    DigitalPotList.clear()
    for file_name in os.listdir(BOX_DIGITAL_POT_PATH):
        if file_name.endswith('.txt'):
            DigitalPotList.append(file_name.replace('.txt',''))
    return DigitalPotList

def sliderColor(self,sliderIndex,minValue,maxValue):
    """_summary_

    Args:
        sliderIndex (_type_): _description_
        minValue (_type_): _description_
        maxValue (_type_): _description_

    Returns:
        _type_: _description_
        

    Color digital pot slider depends value set
    
    """
    sliderValue = eval(f'self.digital_pot{sliderIndex}.value()')
    setColorMax = maxValue/255
    if (sliderValue/setColorMax)>=255:
        G=B=0
        R=255
    elif (sliderValue/setColorMax) <= 10:
        B=255
        R=G = 240 - abs(sliderValue/setColorMax-20)
    else:
        G=B= 255-(sliderValue/setColorMax)
        R =255
       
    return int(R),int(G),int(B)

def sliderColorDac(self,sliderIndex,minValue,maxValue):
    """_summary_

    Args:
        sliderIndex (_type_): _description_
        minValue (_type_): _description_
        maxValue (_type_): _description_

    Returns:
        _type_: _description_
        
    Color Dac slider depends value set   
    """
    colorSlider = eval(f'self.dac_pot{sliderIndex}.value()')
    setColorMax = maxValue/255
    if (colorSlider/setColorMax)>=255:
        G=B=0
        R=255
    elif (colorSlider/setColorMax) <= 10:
        B=255
        R=G = 240 - abs(colorSlider/setColorMax-20)
    else:
        G=B= 255-(colorSlider/setColorMax)
        R =255
       
    return int(R),int(G),int(B)

def listLanguages():
    """
    return all H800 languages
    """
    LIST_LANG =[]
    LIST_LANG.clear()
    for lang in state.ALL_LANGUAGES:
        LIST_LANG.append(f'{str(lang)}')
    return LIST_LANG

def listLanguageCraft():
    """
    return all H800 languages
    """
    LIST_LANG =[]
    LIST_LANG.clear()
    for lang in state.ALL_LANG_CRAFT:
        LIST_LANG.append(f'{str(lang)}')
    return LIST_LANG

def listVariantElements():
    """
    return all variant elements
    """
    LIST_VARIANT =[]
    LIST_VARIANT.clear()
    state.VARIANTS.items()
    for index,lang in enumerate(list(state.VARIANTS.keys())):
        LIST_VARIANT.append(f'{index}-->{str(lang)}')
    return LIST_VARIANT
