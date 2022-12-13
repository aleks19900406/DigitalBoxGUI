import os 
from os.path import abspath, basename, dirname, join, realpath
TEST_DIR_NAME = dirname(abspath(__file__))
TEST_ROOT_NAME = basename(TEST_DIR_NAME)
TEST_ROOT = dirname(TEST_DIR_NAME)
TEST_DATA = dirname(TEST_ROOT)
DATA = dirname(TEST_DATA)
MARKS = os.path.join(TEST_ROOT, "BOX_MARKS")
LOOKUP_TABLE = os.path.join(TEST_ROOT, "data",'digital_box','Table')
print(MARKS )
res =[]

# Iterate directory
for path in os.listdir(MARKS):
    # check if current path is a file
    if path.endswith(".txt"):
        res.append(path.replace('.txt',''))
print(res)
def set_temp_PT1000(temp: int,tableIndex = 1):
    PT1000_file = open(f'{LOOKUP_TABLE}{tableIndex}.txt')
    dict_temp = {}
    for line in PT1000_file:
            value, key = line.split()
            #print(value,key)
            dict_temp[float(key)] = value
    res = int((dict_temp.get(temp)or dict_temp[min(dict_temp.keys(), key=lambda key: abs(key - temp))])
    )
    print('RES',res)


set_temp_PT1000(500,5)