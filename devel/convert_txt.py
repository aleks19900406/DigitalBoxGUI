with open('Table1.2.txt') as f:
    lines = f.readlines()
dict_temp = {}
f = open('Table.txt','w')
for line in lines:
    value, key = line.split()
    dict_temp[float(key)] = value
    print(value, key)
    f.write(f"{key} {value}\n")