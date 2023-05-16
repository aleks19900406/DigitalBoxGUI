print("App for switch digital pot value and readed value. Input just name of the file !!!")
print("Enter txt file you want to convert: ")
txt_file = input()

with open(f'{txt_file}.txt') as f:
    lines = f.readlines()
dict_temp = {}
f = open(f'{txt_file}_convert.txt','w')
for line in lines:
    value, key = line.split()
    dict_temp[float(key)] = value
    f.write(f"{key} {value}\n")