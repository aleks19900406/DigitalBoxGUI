from .local_settings import load_rpi_password

PASSWORD = load_rpi_password()  # not stored in the code: see local_settings.py
ALL_LANGUAGES =['EN-English','DE-German','NL-Nederlands','PL-Polish ','FR-French','IT-Italiano','ES-Spanish','SL-Slovenian','DA-Danish','NO-Norwegian','FI-Finnish',
                'SV-Swedish','RU-Russian','KK-Kazakhstan','UK-Ukraine','CS-Czech','SK-Slovak','HR-Croatian','SR-Serbian','EL-Greek','HU-Hungarian','SCN-Chinese',
                'PT-Portugese','RO-Romanian','BL-Bulgarian','ET-Estonian','LT-Lithuanian','LV-Latvian']
ALL_LANG_CRAFT = [
    "Czech-cs",
    "Danish-da",
    "German-de",
    "Estonian-et",
    "English-en",
    "Spanish-es",
    "French-fr",
    "Croatian-hr",
    "Italian-it",
    "Latvian-lv",
    "Lithuanian-lt",
    "Dutch-nl",
    "Norwegian-no",
    "Polish-pl",
    "Portuguese-pt",
    "Russian-ru",
    "Slovak-sk",
    "Slovenian-sl",
    "Serbian-sr",
    "Finnish-fi",
    "Swedish-sv",
    "Ukrainian-uk",
    "Chinese (Simplified)-zh-CN",
    "Chinese (Traditional)-zh-TW"
]
VARIANTS = {
    "UNKONOWN": 0,
    "P_MF_SS_MW_PY_ATAG_60": 1,
    "P_MF_SS_MW_PY_ASKO_60": 2,
    "P_MF_SS_MW_PY_ALL_60": 3,
    "P_MF_SS_ATAG_60": 4,
    "P_MF_SS_ASKO_60": 5,
    "P_MF_SS_ALL_60": 6,
    "P_MF_MW_PY_ALL_X_60": 7,
    "P_MF_MW_PY_ALL_S_60": 8,
    "P_MF_PY_X_60": 9,
    "P_MF_PY_ASKO_60": 10,
    "P_MF_PY_ALL_X_60": 11,
    "P_MF_PY_ALL_S_60": 12,
    "P_MF_SS_MW_PY_X_ASKO_45": 13,
    "P_MF_SS_MW_PY_S_ASKO_45": 14,
    "P_MF_SS_ATAG_45": 15,
    "P_MF_SS_ASKO_45": 16,
    "P_MF_SS_ALL_45": 17,
    "P_MF_MW_PY_ASKO_45": 18,
    "P_MF_MW_PY_ALL_45": 19,
    "P_SS_ASKO_X_45": 20,
    "P_SS_ASKO_S_45": 21
}
VERZIJA_ESP = "3.40"
VERZIJA_RPI = "3.20"
DIGITAL_BOX_VERSION = 'V5.0'
MAIN_TIME_REFRESHING = 500
MAX_TIME_REFRESHING = 1000
SPACE = '\n'
DigitalInput = 32
change_input = []
for input in range(DigitalInput):
    change_input.append(False)
change_parameters =[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
beginPotValue = [0,0,0,0,0,0]
beginDacValue = [0,0,0,0,0,0,0,0]
beginSetVoltage = [0,0,0,0]
beginSetPot = 0
beginDacPot = 0
setPwm1 = [0,0]
setPwm2 = [0,0]
setPwmOld =[0,0]
errorNumber ='#'*50

DacTableCreate = None
HusaModelWindow = None
PotTableSet = None
PyroSetSystem = None
RunAutoTest = None
SetDacValue = None
autoTest = None
deviceBio24 = None
deviceG800 = None
mainWindow = None
