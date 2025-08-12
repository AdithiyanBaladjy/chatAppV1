import os
import sys
import pandas as pd
import json
rows=[] #array of array containing the cell values in the same order as the input table
headers=["Module","Field Name","API Name","Data Type"]
fullPath='/Users/adithiyan-14770/widgets/python utils/testing automation/Desk_Layout_Getter/'
inputFile=fullPath+'input.json'
inputDict=None
moduleName="Desk"
debug=False
with open(inputFile,'r') as f:
    inputDict=json.load(f)
LayoutSections=inputDict["sections"]
for section in LayoutSections:
    sectionFields=section["fields"]
    for field in sectionFields:
        rowToBeAdded=[moduleName]
        fieldLabel=field["displayLabel"]
        fieldApiName=field["apiName"]
        fieldType=field["type"]
        rowToBeAdded.append(fieldLabel)
        rowToBeAdded.append(fieldApiName)
        rowToBeAdded.append(fieldType)
        rows.append(rowToBeAdded)
    if not debug:
        print(rows)
        debug=True
dataFrame=pd.DataFrame(data=rows,columns=headers)
dataFrame.to_csv(fullPath+"output.csv")
