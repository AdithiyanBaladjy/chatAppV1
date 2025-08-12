from datetime import datetime
import multiprocessing as mp
from projectConstants import projectDir

logsDirectory=projectDir+"logs/"
infoLogLevel="INFO"
warningLogLevel="WARNING"
errorLogLevel="ERROR"
#writes log to the log file
#The log file name will be of the form - dd_mm_yyyy_scheduler_name
#Inputs - componentName - get view trigger/ check Status schedule/ download file schedule/ sftp push schedule
# logLevel - Info, Warning, Error
#LogLine - Log message
def writeLog(componentName,logLevel,LogLine):
    # return
    dateStamp=datetime.now().strftime("%d_%m_%Y")
    timeStamp=datetime.now().strftime("%H:%M:%S")
    logFileName=logsDirectory+dateStamp+"_"+componentName.replace(" ","_")+".txt"
    with open(logFileName,"a+") as fp:
        logLevel=logLevel.upper()
        logLine=timeStamp+": "+logLevel+" "+LogLine+"\n"
        fp.write(logLine)

def writeLogAsync(componentName,logLevel,LogLine):
    logProcess=mp.Process(target=writeLog,args=(componentName,logLevel,LogLine))
    logProcess.start()
    logProcess.join()
    # logProcess.join()
if __name__=="__main__":     
    writeLogAsync("check status schedule","Info","Async logger test 3")