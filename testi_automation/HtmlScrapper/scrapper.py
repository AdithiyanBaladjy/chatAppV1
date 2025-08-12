import os
import sys
from bs4 import BeautifulSoup
import pandas as pd

rows=[] #array of array containing the cell values in the same order as the input table
headers=["Module","Field Name","API Name","Data Type"]
fullPath='/Users/adithiyan-14770/widgets/python utils/testing automation/HtmlScrapper/'
inputFile=fullPath+'inputTable.html'
inputTable=None
moduleName="Loan Accounts"
with open(inputFile,'r') as f:
    inputTable=BeautifulSoup(f,"html.parser")
tables=inputTable.find_all("table")
rowNo=0
for table in tables:
    tableRowsWithoutHeader=table.find_all("tr")[1:]
    for row in tableRowsWithoutHeader:
        tdElements=row.find_all("td")
        rowData=[moduleName]
        cellCount=0
        if(rowNo<2):
            print("Row is ",row)
        for cell in tdElements:
            if(cellCount>2):
                break
            try:
                cellValue=cell.get_text()
                if (rowNo<2):
                    print("CellValue is",cell)
                if((cellValue!=None)and(cellValue!='')):
                    cellValue=cellValue.replace("Edit     Save Cancel  Please exercise caution while changing the name as it may affect the existing integrations","")
                    rowData.append(cellValue)
                    cellCount+=1

            except:
                print("Cell value empty",cell)
                continue
        rows.append(rowData)
        rowNo+=1
dataFrame=pd.DataFrame(data=rows,columns=headers)
dataFrame.to_csv(fullPath+"output.csv")
