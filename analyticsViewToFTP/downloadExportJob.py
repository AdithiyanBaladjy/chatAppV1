from oauthUtils import generateAccessToken
from dbUtils import databaseUtils
import requests
import urllib.parse
import json
import time
from datetime import datetime
import json
from projectConstants import zohoAccountsServerUri,clientId,clientSecret,code,analyticsServerUri,workspaceId,analyticsOrgId,exportJobTableName, exportJobTableSchema, outputFilesDirectory
from projectConstants import sftpServerIp, sftpPassword, sftpUserName,sftpDirectory
from projectConstants import fileDownloadConcurrencyLimit,projectDir,downloadRetryLimit
import pysftp
import asyncio
from loggingUtils import writeLog, infoLogLevel, warningLogLevel, errorLogLevel
from AnalyticsTableUtils_asyncio import asyncUpdateAnalyticsTableWithRetry,InputTableWorkspaceId,InputTableViewId,inputTableOwnerMail,inputTableViewName,inputTableWorkspaceName,asyncUpdateAnalyticsApiV1WithRetry
import traceback


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

#download the file from the download URL
def downloadFileInChunks(accessToken,analyticsOrgId,downloadUrl,viewId,jobId):
    writeLog(componentName,infoLogLevel,"Initiating the download API for the view: "+str(viewId))
    writeLog(componentName,infoLogLevel,"Checking access token")
    accessToken=generateAccessToken.checkAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
    writeLog(componentName,infoLogLevel,"Received access token")

    apiHeader={"ZANALYTICS-ORGID":analyticsOrgId,"Authorization":"Zoho-oauthtoken "+accessToken}
    
    
    writeLog(componentName,infoLogLevel,"View {0}: Checking download API status".format(viewId))
    outputFileName=str(jobId)+"_"+datetime.now().strftime("%d_%m_%Y_%H_%M_%S")+".csv"
    try:
        response=requests.get(downloadUrl,headers=apiHeader,stream=True)
    except requests.exceptions.HTTPError as errh:
        #Http error
        writeLog(componentName,errorLogLevel,"HTTP error in calling download API: "+str(errh))
        return {"status":"network failure"}
    except requests.exceptions.ConnectionError as errc:
        #Connection error
        writeLog(componentName,errorLogLevel,"Connection error in calling download API: "+str(errc))
        return {"status":"network failure"}
    except requests.exceptions.Timeout as errt:
        writeLog(componentName,errorLogLevel,"Time-out error in calling download API: "+str(errt))
        #Time-out error
        return {"status":"network failure"}
    except requests.exceptions.RequestException as err:
        #Generic error
        writeLog(componentName,errorLogLevel,"Error in calling download API: "+str(err))
        return {"status":"network failure"}
    try:
        response.raise_for_status()
    except Exception as e:
        writeLog(componentName,infoLogLevel,"View {0}: Download API failed. Error: {1} API Response: {2}".format(viewId,str(e),json.dumps(response.text)))
        responseObj={}
        responseObj["status"]="Failure"
        responseObj["details"]=response.text
        return responseObj
    writeLog(componentName,infoLogLevel,"View {0}: Download API Success. downloading file chunks".format(viewId))
    try:
        with open(outputFilesDirectory+outputFileName,'wb+') as outFile:
            for chunk in response.iter_content(chunk_size=8192):
                outFile.write(chunk)
        writeLog(componentName,infoLogLevel,"View {0}: Download completed.".format(viewId))
        return {"status":"Success","fileName":outputFileName}
    except requests.exceptions.ConnectionError as errc:
        #Connection error
        writeLog(componentName,errorLogLevel,"Connection error in downloading file in chunks. Error: "+str(errc))
        return {"status":"network failure"}
    except requests.exceptions.RequestException as err:
        #Generic error
        writeLog(componentName,errorLogLevel,"Exception in downloading file in chunks. Error: "+str(err))
        return {"status":"network failure"}

#Export given file to sftp location
def pushFileToSftp(sftpServrIp,sftpUserName,sftpPassword,fileName):
    
    sftpConn=pysftp.Connection(host=sftpServrIp,username=sftpUserName,password=sftpPassword)
    # with sftpConn.cwd(sftpDirectory):
    # sftpConn.put(outputFilesDirectory+fileName)
    sftpConn.cwd(sftpDirectory)
    sftpConn.put(outputFilesDirectory+fileName)
    # print(sftpConn.listdir())
    sftpConn.close()

#download file and update DB
async def downloadFileUpdateDb(dbConnection,jobId,oauthToken,downloadUrl,viewId,requestId,downloadTryCount):
    global asyncTasksList
    writeLog(componentName,infoLogLevel,"Async download starts for jobId:"+str(jobId))
    rowUpdateDict={}
    rowUpdateDict["underProcess"]=1
    writeLog(componentName,infoLogLevel,"Updating DB for starting file download for jobId:"+str(jobId))
    dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,rowUpdateDict)
    loop = asyncio.get_event_loop()
    jobStatusResp=await loop.run_in_executor(None,lambda: downloadFileInChunks(oauthToken,analyticsOrgId,downloadUrl,viewId,jobId))
    downloadTryCount+=1
    print("File Downloaded")
    print(jobStatusResp)

    if(jobStatusResp["status"]=="network failure"):
        if(downloadTryCount>=downloadRetryLimit):
            downloadFailedDetails="'Download retry limit reached'"
            completedUpdateDict=dict()
            completedUpdateDict["jobStatus"]="'failed file download'"
            completedUpdateDict["underProcess"]=0
            completedUpdateDict["failureLog"]=downloadFailedDetails
            completedUpdateDict["downloadTryCount"]=downloadTryCount
            writeLog(componentName,errorLogLevel,"Updating DB for the download failed status for jobId:"+str(jobId))
            updateResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,completedUpdateDict)
            writeLog(componentName,errorLogLevel,"job id:{0}: Updating download failed status in Analytics table".format(jobId))

            tableWriteBack={}
            tableWriteBack["RequestStatus"]="File download failure"
            tableWriteBack["DownloadErrorLog"]=downloadFailedDetails
            tableWriteBack["downloadTryCount"]=downloadTryCount
            updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,requestId,tableWriteBack)
            asyncTasksList.append(updateTask)
        else:
            completedUpdateDict=dict()
            completedUpdateDict["underProcess"]=0
            completedUpdateDict["downloadTryCount"]=downloadTryCount
            writeLog(componentName,infoLogLevel,"Queuing the job for retry later jobId:"+str(jobId))
            updateResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,completedUpdateDict)
            writeLog(componentName,infoLogLevel,"job id:{0}: Updating download try count:{1} in Analytics table".format(jobId,downloadTryCount))
            analyticsUpdateDict=dict()
            analyticsUpdateDict["downloadTryCount"]=downloadTryCount
            # asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,analyticsUpdateDict,None)
            updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,requestId,analyticsUpdateDict)
            asyncTasksList.append(updateTask)
    elif(jobStatusResp["status"]=="Success"):
        fileName=jobStatusResp["fileName"]
        completedUpdateDict=dict()
        completedUpdateDict["localFileName"]="'"+fileName+"'"
        completedUpdateDict["jobStatus"]="'file downloaded'"
        completedUpdateDict["underProcess"]=0
        completedUpdateDict["downloadTryCount"]=downloadTryCount
        writeLog(componentName,infoLogLevel,"Updating DB for the download success status for jobId:"+str(jobId))
        updateResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,completedUpdateDict)
        writeLog(componentName,infoLogLevel,"DB update response for the download success status for jobId:"+str(jobId)+str(updateResp))
        writeLog(componentName,infoLogLevel,"job id:{0}: Updating request status in Analytics table".format(jobId))
        tableWriteBack={}
        tableWriteBack["RequestStatus"]="Queued for SFTP push"
        tableWriteBack["fileGeneratedDateTime"]=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        tableWriteBack["generatedFileName"]=fileName
        tableWriteBack["downloadTryCount"]=downloadTryCount
        task=asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,tableWriteBack,"dd/MM/yyyy HH:mm:ss")
        asyncTasksList.append(task)
    else:
        downloadFailedDetails="'"+json.dumps(jobStatusResp["details"])+"'"
        completedUpdateDict=dict()
        completedUpdateDict["jobStatus"]="'failed file download'"
        completedUpdateDict["underProcess"]=0
        completedUpdateDict["downloadTryCount"]=downloadTryCount
        completedUpdateDict["failureLog"]=downloadFailedDetails
        writeLog(componentName,infoLogLevel,"Updating DB for the download failed status for jobId:"+str(jobId))
        updateResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,completedUpdateDict)
        writeLog(componentName,infoLogLevel,"job id:{0}: Updating request status in Analytics table".format(jobId))

        tableWriteBack={}
        tableWriteBack["RequestStatus"]="File download failure"
        tableWriteBack["DownloadErrorLog"]=downloadFailedDetails
        tableWriteBack["downloadTryCount"]=downloadTryCount
        updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,requestId,tableWriteBack)
        asyncTasksList.append(updateTask)
        #asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,{"RequestStatus":"File download failure"})
    print("File download status updated")
    

#main function
async def main():
    global asyncTasksList
    writeLog(componentName,infoLogLevel,"Schedule Started")
    dbConnection=databaseUtils.getDbConnection()
   
    writeLog(componentName,infoLogLevel,"Creating table if not exists")
    databaseUtils.createTableIfNotExists(dbConnection,exportJobTableName,exportJobTableSchema)
    try:
        writeLog(componentName,infoLogLevel,"Generating access token")
        accessToken=generateAccessToken.getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
        print(accessToken)
        oauthToken=accessToken["accessToken"]

        # exportViewResp=getAnalyticsView(analyticsOrgId,analyticsServerUri,oauthToken,workspaceId,viewId)
        # exportViewResp=getStoredResponse("exportApiResp.json")
        #continue from here
        columnsList=["jobId","viewId","downloadUrl","RequestId","downloadTryCount"]
        writeLog(componentName,infoLogLevel,"Getting completed jobs from DB")
        jobsList=databaseUtils.getCompletedJobs(dbConnection,exportJobTableName,2,columnsList)
        writeLog(componentName,infoLogLevel,"Read "+str(len(jobsList))+" jobs")
        tasksList=[]
        for jobTuple in jobsList:
            jobId=jobTuple[0]
            viewId=jobTuple[1]
            downloadUrl=jobTuple[2]
            requestId=jobTuple[3]
            downloadTryCount=jobTuple[4] if jobTuple[4] is not None else 0
            writeLog(componentName,infoLogLevel,"Creating async download task for jobID: "+str(jobId))
            task=asyncio.create_task(downloadFileUpdateDb(dbConnection,jobId,oauthToken,downloadUrl,viewId,requestId,downloadTryCount))
            tasksList.append(task)
        tasksLen=len(tasksList)
        writeLog(componentName,infoLogLevel,"Created {0} async download tasks".format(str(len(tasksList))))
        taskCount=0
        while(taskCount<tasksLen):
            for _ in range(fileDownloadConcurrencyLimit):
                if(taskCount<tasksLen):
                    task=tasksList[taskCount]
                    writeLog(componentName,infoLogLevel,"Executing async download task:{0}".format(str(taskCount)))
                    await task
                taskCount+=1

    except Exception as err:
        print("Error in data generation",err)
        writeLog(componentName,errorLogLevel,"Error in download schedule:{0}".format(traceback.format_exc()))
    dbConnection.close()
    writeLog(componentName,infoLogLevel,"Schedule Ended")
    writeLog(componentName,infoLogLevel,"Awaiting async update tasks. Tasks created {0}".format(len(asyncTasksList)))
    for t in asyncTasksList:
        await t
    


if __name__=="__main__":
    #Global variables
    asyncTasksList=[]
    componentName="download file schedule"
    asyncio.run(main())