from os import listdir, remove
from os.path import isfile,join, getctime, exists, getmtime
from projectConstants import fileExportsDir,fileCleanUpLimitInSecs, logsDir, logCleanUpLimitInSecs
import time
from loggingUtils import writeLog,infoLogLevel,warningLogLevel, errorLogLevel
import datetime
import traceback

def getFileExportsForDeletion():
    writeLog(componentName,infoLogLevel,"Getting export files for deletion")
    print("Getting File Exports for deletion")
    files=[f for f in listdir(fileExportsDir) if isfile(join(fileExportsDir,f))]
    for file in files:
        fileFullPath=join(fileExportsDir,file)
        print("File is",fileFullPath)
        if(exists(fileFullPath)):
            modifiedTime=getmtime(join(fileExportsDir,file))   
            currentTimeInSecs=time.time()
            if(currentTimeInSecs-modifiedTime>fileCleanUpLimitInSecs):
                remove(fileFullPath)
                writeLog(componentName,infoLogLevel,"Removed export file: "+str(fileFullPath))
                writeLog(componentName,infoLogLevel,"File Modified on:"+str(datetime.datetime.fromtimestamp(modifiedTime)))
                

def getLogFilesForDeletion():
    files=[f for f in listdir(logsDir) if isfile(join(logsDir,f))]
    for file in files:
        fileFullPath=join(logsDir,file)
        if(exists(fileFullPath)):
            modifiedTime=getmtime(join(logsDir,file))    
            currentTimeInSecs=time.time()
            if(currentTimeInSecs-modifiedTime>logCleanUpLimitInSecs):
                remove(fileFullPath)
                writeLog(componentName,infoLogLevel,"Removed Log file: "+str(fileFullPath))
                writeLog(componentName,infoLogLevel,"File Modified on:"+str(datetime.datetime.fromtimestamp(modifiedTime)))
               
            


if __name__ == "__main__":
    componentName="Logs & Files Clean-Up Job"
    writeLog(componentName,infoLogLevel,"Deletion Job Started")
    getLogFilesForDeletion()
    getFileExportsForDeletion()