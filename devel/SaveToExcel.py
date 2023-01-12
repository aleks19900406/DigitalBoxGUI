
# import openpyxl module 
import openpyxl 
import random 
print(random.randint(0,10))
indexFile = 0
value = 0
# Call a Workbook() function of openpyxl 
# to create a new blank Workbook object 
wb = openpyxl.Workbook() 
# Get workbook active sheet 
# from the active attribute 
sheet = wb.active 
# Cell objects also have row, column 
# and coordinate attributes that provide 
# location information for the cell. 
  
# Note: The first row or column integer 
# is 1, not 0. Cell object is created by 
# using sheet object's cell() method. 
for index in range(1,20):
    c1 = sheet.cell(row = 1, column = index) 
    # writing values to cells 
    c1.value = f"name{index}"

for rowMove in range(1,500):
    value +=1
    for index in range(1,20):
        c2 = sheet.cell(row = 1+value, column = index) 
        #c2.value = random.randint(-122,1022)
        c2.value = rowMove
        if value > 50 :
            value = 0
            indexFile +=1
            wb.save(f"excelFile/sample{indexFile}.xlsx")
            print('new file',indexFile)
    #print('rowMove',rowMove)
wb.save(f"excelFile/sample.xlsx")
    
# Anytime you modify the Workbook object 
# or its sheets and cells, the spreadsheet 
# file will not be saved until you call 
# the save() workbook method. 
