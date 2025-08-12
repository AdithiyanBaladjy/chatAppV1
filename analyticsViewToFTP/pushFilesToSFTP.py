from oauthUtils import generateAccessToken
from dbUtils import databaseUtils
import requests
import urllib.parse
import json
import time
from datetime import datetime
import json
from projectConstants import zohoAccountsServerUri,clientId,clientSecret,code,analyticsServerUri,workspaceId,analyticsOrgId,exportJobTableName, exportJobTableSchema, outputFilesDirectory
from projectConstants import sftpServerIp, sftpPassword, sftpUserName,sftpDirectory, completedJobsReadCount
from projectConstants import sftpConcurrentConnectionsCount,sftpRetryLimit,fileExportsDir
import pysftp
import asyncio
from loggingUtils import writeLog,infoLogLevel,warningLogLevel, errorLogLevel
from AnalyticsTableUtils_asyncio import asyncUpdateAnalyticsTableWithRetry,InputTableWorkspaceId,InputTableViewId,inputTableViewName,inputTableOwnerMail,inputTableWorkspaceName,asyncUpdateAnalyticsApiV1WithRetry
import paramiko
import traceback
import os


#testing function
def getStoredResponse(fileName):
    apiResp=None
    with open(fileName,"r") as fp:
        apiResp=json.load(fp)
    return apiResp

#Creates a bulk export job request
#can raise exception
def getAnalyticsView(analyticsOrgId,analyticsServerUri,accessToken,workspaceId,viewId):
    configJson={"responseFormat":"csv"}
    configJsonUrlEncoded=urllib.parse.quote_plus(str(configJson))
    exportViewUrl="https://"+analyticsServerUri+"/restapi/v2/bulk/workspaces/"+workspaceId+"/views/"+viewId+"/data?CONFIG="+configJsonUrlEncoded
    apiHeader={"ZANALYTICS-ORGID":analyticsOrgId,"Authorization":"Zoho-oauthtoken "+accessToken}
    apiResp=requests.get(exportViewUrl,headers=apiHeader)
    apiRespDict=json.loads(apiResp.text)
    return apiRespDict
    

#gets the status of given bulk export job
def getExportJobStatus(analyticsOrgId,analyticsServerUri,accessToken,workspaceId,jobId):
    apiHeader={"ZANALYTICS-ORGID":analyticsOrgId,"Authorization":"Zoho-oauthtoken "+accessToken}
    getStatusUrl="https://"+analyticsServerUri+"/restapi/v2/bulk/workspaces/"+str(workspaceId)+"/exportjobs/"+str(jobId)
    apiResp=requests.get(getStatusUrl,headers=apiHeader)
    apiRespDict=json.loads(apiResp.text)
    return apiRespDict

#Read the contents of a local file in chunks
def readInChunks(fileObj,chunkSize=1024):
    while True:
        data=fileObj.read(chunkSize)
        if not data:
            break
        yield data

#Export given file to SFTP location in chunks
def pushFileToSftpInChunks(sftpServrIp,sftpUserName,sftpPassword,fileName):
    sshClient=paramiko.SSHClient()
    sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        sshClient.connect(hostname=sftpServrIp,port=22,username=sftpUserName,password=sftpPassword)
    except Exception as excp:
        #Raise error: Couldn't take SSH session of the SFTP server
        pass
        return
    try:
        sftpClient=sshClient.open_sftp()
        sftpClient.chdir(sftpDirectory)
        localFile=open(outputFilesDirectory+fileName,mode='r')
        with sftpClient.file(fileName,mode='w',bufsize=1024) as remoteFile:
            for fileChunk in readInChunks(localFile):
                remoteFile.write(fileChunk)
        localFile.close()

    except Exception as ex:
        #Raise error: SFTP connection failed
        return
    sshClient.close()

#Export given file to sftp location
def pushFileToSftp(sftpServrIp,sftpUserName,sftpPassword,fileName):
    writeLog(componentName,infoLogLevel,"File Name:{0} Async SFTP push task started".format(str(fileName)))
    try:
        writeLog(componentName,infoLogLevel,"File Name:{0} Initiating SFTP connection".format(str(fileName)))
        sftpConn=pysftp.Connection(host=sftpServrIp,username=sftpUserName,password=sftpPassword)
        # with sftpConn.cwd(sftpDirectory):
        # sftpConn.put(outputFilesDirectory+fileName)
        writeLog(componentName,infoLogLevel,"File Name:{0} SFTP connection established".format(str(fileName)))
        sftpConn.cwd(sftpDirectory)
        writeLog(componentName,infoLogLevel,"File Name:{0} reached target SFTP directory".format(str(fileName)))
        sftpConn.put(outputFilesDirectory+fileName)
        # print(sftpConn.listdir())
        writeLog(componentName,infoLogLevel,"File Name:{0} SFTP write completed".format(str(fileName)))
        sftpConn.close()
        outputDict={}
        outputDict["status"]="success"
        return outputDict
    except Exception as e:
        writeLog(componentName,errorLogLevel,"File Name:{0} error in SFTP connection".format(traceback.format_exc()))
        outputDict={}
        outputDict["status"]="failure"
        outputDict["errorDetails"]=traceback.format_exc()
        return outputDict
#Delete the given file from the FileExports directory
#delete either push failed or push succedded file
def deleteExportedFile(fileName):
    writeLog(componentName,infoLogLevel,"Attempting to delete exported file:"+fileName)
    if os.path.exists(fileExportsDir+fileName):
        os.remove(fileExportsDir+fileName)
        writeLog(componentName,infoLogLevel,"Exported file deleted: "+fileName)
    else:
        writeLog(componentName,warningLogLevel,"Could not find given file:"+fileExportsDir+fileName)

#push file to Sftp asynchronously
async def asyncSftpPushUpdateDb(dbConnection,jobId,sftpServerIp,sftpUserName,sftpPassword,fileName,requestId,sftpPushCount):
    writeLog(componentName,infoLogLevel,"Async sftp push task starts for jobId:"+str(jobId))
    global asyncTasksList
    loop = asyncio.get_event_loop()
    jobStatusResp=await loop.run_in_executor(None,lambda: pushFileToSftp(sftpServerIp,sftpUserName,sftpPassword,fileName))
    # jobStatusResp=downloadFileInChunks(oauthToken,analyticsOrgId,downloadUrl,viewId)
    sftpPushCount+=1
    print("File Downloaded")
    print(jobStatusResp)
    if(jobStatusResp["status"]=="success"):
        writeLog(componentName,infoLogLevel,"JobId:{0} Async SFTP push task success".format(str(jobId)))
        completedUpdateDict=dict()
        completedUpdateDict["jobStatus"]="'pushed to SFTP'"
        completedUpdateDict["underProcess"]=0
        completedUpdateDict["pushedToSFTP"]=1
        completedUpdateDict["SFTPPushTimeReal"]=time.time()
        completedUpdateDict["SFTPPushTimeInText"]=datetime.now().strftime("'%d-%m-%YT%H:%M:%S'")
        completedUpdateDict["sftpPushCount"]=sftpPushCount
        writeLog(componentName,infoLogLevel,"JobId:{0} Updating DB about Async SFTP push task success".format(str(jobId)))
        dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,completedUpdateDict)
        print("File download status updated")
        writeLog(componentName,infoLogLevel,"job id:{0}: Updating request status in Analytics table".format(jobId))
        tableWriteBack={}
        tableWriteBack["RequestStatus"]="Pushed to SFTP"
        tableWriteBack["sftpPushCount"]=sftpPushCount
        tableWriteBack["sftpPushedDateTime"]=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        updateTask=asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,tableWriteBack,"dd/MM/yyyy HH:mm:ss")
        asyncTasksList.append(updateTask)
        #delete the file pushed
        deleteExportedFile(fileName)
    else:
        if(sftpPushCount>=sftpRetryLimit):
            writeLog(componentName,errorLogLevel,"JobId:{0} SFTP push task failed. Push Limit reached:{1}".format(str(jobId),sftpPushCount))
            
            completedUpdateDict=dict()
            completedUpdateDict["underProcess"]=0
            completedUpdateDict["jobStatus"]="'SFTP push failure'"
            completedUpdateDict["sftpPushCount"]=sftpPushCount
            dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,completedUpdateDict)    
            writeLog(componentName,errorLogLevel,"job id:{0}: Updating SFTP Push failure status in Analytics table".format(jobId))
            tableWriteBack={}
            tableWriteBack["sftpPushCount"]=sftpPushCount
            tableWriteBack["RequestStatus"]="'SFTP push failure'"
            tableWriteBack["sftpPushErrorLog"]="'SFTP push retry limit reached'. Error: "+jobStatusResp["errorDetails"]
            updateTask=asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,tableWriteBack,None)
            asyncTasksList.append(updateTask)
            #delete the file generated
            deleteExportedFile(fileName)
        else:
            writeLog(componentName,errorLogLevel,"JobId:{0} Async SFTP push task failed. queuing task for retry. Retry count:{1}".format(str(jobId),sftpPushCount))
            completedUpdateDict=dict()
            completedUpdateDict["underProcess"]=0
            completedUpdateDict["sftpPushCount"]=sftpPushCount
            dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,completedUpdateDict)    
            writeLog(componentName,infoLogLevel,"job id:{0}: Updating request status in Analytics table".format(jobId))
            tableWriteBack={}
            tableWriteBack["sftpPushCount"]=sftpPushCount
            tableWriteBack["sftpPushErrorLog"]=jobStatusResp["errorDetails"]
            updateTask=asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,tableWriteBack,None)
            asyncTasksList.append(updateTask)
#old main function
async def main():
    global asyncTasksList
    writeLog(componentName,infoLogLevel,"Schedule Started")
    dbConnection=databaseUtils.getDbConnection()
    writeLog(componentName,infoLogLevel,"Created DB connection")
   
    writeLog(componentName,infoLogLevel,"Creating table in DB if not exists")
    databaseUtils.createTableIfNotExists(dbConnection,exportJobTableName,exportJobTableSchema)
    try:
        columnsList=["jobId","viewId","localFileName","RequestId","sftpPushCount"]
        writeLog(componentName,infoLogLevel,"Getting jobs to push from DB")
        jobsList=databaseUtils.getJobsToPushSftp(dbConnection,exportJobTableName,completedJobsReadCount,columnsList)
        writeLog(componentName,infoLogLevel,"Read "+str(len(jobsList))+" jobs")
        jobsCount=0
        tasksList=[]
        taskCount=0
        for jobTuple in jobsList:
            jobId=jobTuple[0]
            viewId=jobTuple[1]
            localFileName=jobTuple[2]
            requestId=jobTuple[3]
            sftpPushCount=jobTuple[4] if jobTuple[4] is not None else 0
            writeLog(componentName,infoLogLevel,"Creating async sftp push task for jobID: "+str(jobId))
            task=asyncio.create_task(asyncSftpPushUpdateDb(dbConnection,jobId,sftpServerIp,sftpUserName,sftpPassword,localFileName,requestId,sftpPushCount))
            tasksList.append(task)
        writeLog(componentName,infoLogLevel,"Created {0} async sftp push tasks".format(str(len(tasksList))))
        while(taskCount<len(tasksList)):
            for _ in range(sftpConcurrentConnectionsCount):
                if taskCount<len(tasksList):
                    task=tasksList[taskCount]
                    writeLog(componentName,infoLogLevel,"Executing async status check task:{0}".format(str(taskCount)))
                    await task
                taskCount+=1
            
    except Exception as err:
        print("Error in data generation",err)
        writeLog(componentName,errorLogLevel,"Error in sftp push schedule:{0}".format(traceback.format_exc()))
    dbConnection.close()
    writeLog(componentName,infoLogLevel,"Schedule Ended")
    writeLog(componentName,infoLogLevel,"Awaiting async update tasks. Tasks created {0}".format(len(asyncTasksList)))
    for t in asyncTasksList:
        await t


if __name__=="__main__":
    #Global variables
    asyncTasksList=[]
    componentName="sftp push schedule"
    asyncio.run(main())