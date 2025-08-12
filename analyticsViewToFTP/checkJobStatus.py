from oauthUtils import generateAccessToken
from dbUtils import databaseUtils
import requests
import urllib.parse
import json
import time
from datetime import datetime
import json
from projectConstants import zohoAccountsServerUri,clientId,clientSecret,code,analyticsServerUri,workspaceId,analyticsOrgId,exportJobTableName, exportJobTableSchema
from projectConstants import IncompleteJobsReadCount,exportJobStatusCheckConcurrentConnections, statusCheckRetryLimit
import asyncio
from loggingUtils import writeLog,infoLogLevel,warningLogLevel, errorLogLevel
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
    
async def asyncGetUrl(url,header):
    return await requests.get(url,headers=header)

#gets the status of given bulk export job
async def getExportJobStatus(analyticsOrgId,analyticsServerUri,accessToken,workspaceId,jobId):
    writeLog(componentName,infoLogLevel,"Checking export job status API for jobId"+str(jobId))
    writeLog(componentName,infoLogLevel,"Checking access token")
    accessToken=generateAccessToken.checkAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
    writeLog(componentName,infoLogLevel,"Received access token")
    apiHeader={"ZANALYTICS-ORGID":analyticsOrgId,"Authorization":"Zoho-oauthtoken "+accessToken}
    getStatusUrl="https://"+analyticsServerUri+"/restapi/v2/bulk/workspaces/"+str(workspaceId)+"/exportjobs/"+str(jobId)
    writeLog(componentName,infoLogLevel,"job id:{0}: Getting async event loop".format(jobId))
    loop = asyncio.get_event_loop()
    writeLog(componentName,infoLogLevel,"job id:{0}: Scheduling async API call for status check".format(jobId))
    try:
        apiResp=await loop.run_in_executor(None,lambda: requests.get(getStatusUrl,headers=apiHeader))
    except requests.exceptions.HTTPError as errh:
        #Http error
        writeLog(componentName,errorLogLevel,"HTTP error in calling export API: "+str(errh))
        return {"status":"network failure"}
    except requests.exceptions.ConnectionError as errc:
        #Connection error
        writeLog(componentName,errorLogLevel,"Connection error in calling export API: "+str(errc))
        return {"status":"network failure"}
    except requests.exceptions.Timeout as errt:
        writeLog(componentName,errorLogLevel,"Time-out error in calling export API: "+str(errt))
        #Time-out error
        return {"status":"network failure"}
    except requests.exceptions.RequestException as err:
        #Generic error
        writeLog(componentName,errorLogLevel,"Error in calling export API: "+str(err))
        return {"status":"network failure"}
    writeLog(componentName,infoLogLevel,"job id:{0}: Response obtained from job status API".format(jobId))
    apiRespDict=json.loads(apiResp.text)
    return apiRespDict
#gets export job status and update the table
async def getExportJobStatusUpdateTable(dbConnection,analyticsOrgId,analyticsServerUri,oauthToken,workspaceId,jobId,requestId,statusCheckCount):
    global asyncTasksList
    writeLog(componentName,infoLogLevel,"Async status check starts for jobId:"+str(jobId))
    jobStatusResp=await getExportJobStatus(analyticsOrgId,analyticsServerUri,oauthToken,workspaceId,jobId)
    statusCheckCount+=1
    print("Job response",jobStatusResp)
    writeLog(componentName,infoLogLevel,"job id:{0}: Checking response status".format(jobId))
    respKeys=jobStatusResp.keys()
    if("status" not in respKeys):
        writeLog(componentName,errorLogLevel,"job id:{0}: API response unexpected. Response: {1}".format(jobId,json.dumps(jobStatusResp)))
        #check if statusCheckCount >= statusCheckRetryLimit then update as failure
        if(statusCheckCount>=statusCheckRetryLimit):
            updateDict=dict()
            errorStr="'Status check retries exceeded allowed status check retry limit: {0}'".format(statusCheckRetryLimit)
            updateDict["jobStatus"]="'failure'"
            updateDict["failureLog"]=errorStr
            updateDict["statusCheckCount"]=statusCheckCount
            writeLog(componentName,errorLogLevel,"job id:{0}: Updating retry failure job status in DB".format(jobId,json.dumps(jobStatusResp)))
            dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,updateDict)
            
            writeLog(componentName,errorLogLevel,"job id:{0}: Updating retry failure status in Analytics table".format(jobId))
            analyticsUpdateDict=dict()
            analyticsUpdateDict["RequestStatus"]="File generation failure"
            analyticsUpdateDict["checkStatusErrorLog"]=errorStr
            analyticsUpdateDict["statusCheckCount"]=statusCheckCount
            # asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,analyticsUpdateDict,None)
            updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,requestId,analyticsUpdateDict)
            asyncTasksList.append(updateTask)
        else:
            updateDict=dict()
            updateDict["statusCheckCount"]=statusCheckCount
            writeLog(componentName,infoLogLevel,"job id:{0}: Updating status check count: {1} in DB".format(jobId,statusCheckCount))
            dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,updateDict)
            
            writeLog(componentName,infoLogLevel,"job id:{0}: Updating status check count: {1} in Analytics Input Table".format(jobId,statusCheckCount))
            analyticsUpdateDict=dict()
            analyticsUpdateDict["statusCheckCount"]=statusCheckCount
            # asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,analyticsUpdateDict,None)
            updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,requestId,analyticsUpdateDict)
            asyncTasksList.append(updateTask)
        return
    if(jobStatusResp["status"]=="network failure"):
        #check if statusCheckCount >= statusCheckRetryLimit then update as failure
        writeLog(componentName,errorLogLevel,"job id:{0}: network failure in job status check. Details: {1}".format(jobId,json.dumps(jobStatusResp)))
        if(statusCheckCount>=statusCheckRetryLimit):
            updateDict=dict()
            errorStr="'Status check retries exceeded allowed status check retry limit: {0}'".format(statusCheckRetryLimit)
            updateDict["jobStatus"]="'failure'"
            updateDict["failureLog"]=errorStr
            updateDict["statusCheckCount"]=statusCheckCount
            writeLog(componentName,errorLogLevel,"job id:{0}: Updating retry failure job status in DB".format(jobId,json.dumps(jobStatusResp)))
            dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,updateDict)
            
            writeLog(componentName,errorLogLevel,"job id:{0}: Updating retry failure status in Analytics table".format(jobId))
            analyticsUpdateDict=dict()
            analyticsUpdateDict["RequestStatus"]="File generation failure"
            analyticsUpdateDict["checkStatusErrorLog"]=errorStr
            analyticsUpdateDict["statusCheckCount"]=statusCheckCount
            # asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,analyticsUpdateDict,None)
            updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,requestId,analyticsUpdateDict)
            asyncTasksList.append(updateTask)
        else:
            updateDict=dict()
            updateDict["statusCheckCount"]=statusCheckCount
            writeLog(componentName,infoLogLevel,"job id:{0}: Updating status check count: {1} in DB".format(jobId,statusCheckCount))
            dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,updateDict)
            
            writeLog(componentName,infoLogLevel,"job id:{0}: Updating status check count: {1} in Analytics Input Table".format(jobId,statusCheckCount))
            analyticsUpdateDict=dict()
            analyticsUpdateDict["statusCheckCount"]=statusCheckCount
            # asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,analyticsUpdateDict,None)
            updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,requestId,analyticsUpdateDict)
            asyncTasksList.append(updateTask)
        pass
    elif(jobStatusResp["status"]=="failure"):
        #update the job record as failed and save the errorLog into DB
        writeLog(componentName,errorLogLevel,"job id:{0}: API response failed. Response: {1}".format(jobId,json.dumps(jobStatusResp)))
        updateDict=dict()
        errorStr="'"+json.dumps(jobStatusResp)+"'"
        updateDict["jobStatus"]="'failure'"
        updateDict["failureLog"]=errorStr
        updateDict["statusCheckCount"]=statusCheckCount
        writeLog(componentName,errorLogLevel,"job id:{0}: Updating failure job status in DB".format(jobId,json.dumps(jobStatusResp)))
        dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,updateDict)
        print(dbResp)
        writeLog(componentName,infoLogLevel,"job id:{0}: Updating request status in Analytics table".format(jobId))
        analyticsUpdateDict=dict()
        analyticsUpdateDict["RequestStatus"]="File generation failure"
        analyticsUpdateDict["checkStatusErrorLog"]=errorStr
        analyticsUpdateDict["statusCheckCount"]=statusCheckCount
        updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,requestId,analyticsUpdateDict)
        asyncTasksList.append(updateTask)
    elif(jobStatusResp["status"]=="success"):
        writeLog(componentName,infoLogLevel,"job id:{0}: API response success.".format(jobId))
        dataDict=jobStatusResp["data"]
        jobStatus=dataDict["jobStatus"]
        if(jobStatus=="JOB COMPLETED"):
            writeLog(componentName,infoLogLevel,"job id:{0}: Job completed.".format(jobId))
            downloadUrl=dataDict["downloadUrl"]
            downloadExpiry=dataDict["expiryTime"]
            completedUpdateDict=dict()
            completedUpdateDict["jobStatus"]="'file generated'"
            completedUpdateDict["downloadUrl"]="'"+downloadUrl+"'"
            completedUpdateDict["downloadExpiryTime"]=downloadExpiry
            completedUpdateDict["jobCompletedTimeReal"]=time.time()
            completedUpdateDict["jobCompletedTimeInText"]=datetime.now().strftime("'%d-%m-%YT%H:%M:%S'")
            completedUpdateDict["statusCheckCount"]=statusCheckCount
            writeLog(componentName,infoLogLevel,"job id:{0}: Updating DB of job status".format(jobId))
            dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,completedUpdateDict)
            writeLog(componentName,infoLogLevel,"job id:{0}: Job status in DB updated".format(jobId)) 
            writeLog(componentName,infoLogLevel,"job id:{0}: Updating request status in Analytics table".format(jobId))
            tableWriteBack={}
            tableWriteBack["RequestStatus"]="File generated"
            tableWriteBack["statusCheckCount"]=statusCheckCount
            tableWriteBack["jobCompletedDateTime"]=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            updateTask=asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,tableWriteBack,"dd/MM/yyyy HH:mm:ss")   
            asyncTasksList.append(updateTask)
        elif(jobStatus=="JOB IN PROGRESS"):
            #retry count check
            writeLog(componentName,infoLogLevel,"job id:{0}: JOB IN PROGRESS".format(jobId))
            if(statusCheckCount>=statusCheckRetryLimit):
                updateDict=dict()
                errorStr="'Status check retries exceeded allowed status check retry limit: {0}'".format(statusCheckRetryLimit)
                updateDict["jobStatus"]="'failure'"
                updateDict["failureLog"]=errorStr
                updateDict["statusCheckCount"]=statusCheckCount
                writeLog(componentName,errorLogLevel,"job id:{0}: Updating retry failure job status in DB".format(jobId,json.dumps(jobStatusResp)))
                dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,updateDict)
            
                writeLog(componentName,errorLogLevel,"job id:{0}: Updating retry failure status in Analytics table".format(jobId))
                analyticsUpdateDict=dict()
                analyticsUpdateDict["RequestStatus"]="File generation failure"
                analyticsUpdateDict["checkStatusErrorLog"]=errorStr
                analyticsUpdateDict["statusCheckCount"]=statusCheckCount
                # asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,analyticsUpdateDict,None)
                updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,requestId,analyticsUpdateDict)
                asyncTasksList.append(updateTask)
            else:
                updateDict=dict()
                updateDict["statusCheckCount"]=statusCheckCount
                writeLog(componentName,infoLogLevel,"job id:{0}: Updating status check count: {1} in DB".format(jobId,statusCheckCount))
                dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,updateDict)
            
                writeLog(componentName,infoLogLevel,"job id:{0}: JOB IN PROGRESS".format(jobId))
                writeLog(componentName,infoLogLevel,"job id:{0}: Updating request status in Analytics table".format(jobId))
                tableWriteBack={}
                tableWriteBack["RequestStatus"]="Job in progress"
                tableWriteBack["statusCheckCount"]=statusCheckCount
                updateTask=asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,tableWriteBack,None)
                asyncTasksList.append(updateTask)
        elif(jobStatus=="ERROR OCCURRED"):
            #job failed
            #write error log and change job status to failed
            writeLog(componentName,errorLogLevel,"job id:{0}: API response failed. Response: {1}".format(jobId,json.dumps(jobStatusResp)))
            updateDict=dict()
            errorStr="'"+json.dumps(jobStatusResp)+"'"
            updateDict["jobStatus"]="'failure'"
            updateDict["failureLog"]=errorStr
            updateDict["statusCheckCount"]=statusCheckCount
            writeLog(componentName,errorLogLevel,"job id:{0}: Updating failure job status in DB".format(jobId,json.dumps(jobStatusResp)))
            dbResp=databaseUtils.updateByJobId(dbConnection,exportJobTableName,jobId,updateDict)
            print(dbResp)
            writeLog(componentName,infoLogLevel,"job id:{0}: Updating request status in Analytics table".format(jobId))
            tableWriteBack={}
            tableWriteBack["RequestStatus"]="File generation failure"
            tableWriteBack["CheckStatusErrorLog"]=errorStr
            tableWriteBack["statusCheckCount"]=statusCheckCount
            updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,requestId,tableWriteBack)
            #asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,requestId,tableWriteBack)
            asyncTasksList.append(updateTask)
        else:
            respStr="'"+json.dumps(jobStatusResp)+"'"
            writeLog(componentName,warningLogLevel,"job id:{0}: Unexpected Job status. Response: {1}".format(jobId,respStr))
    
async def main():
    global asyncTasksList
    writeLog(componentName,infoLogLevel,"Async Main Function started")
    dbConnection=databaseUtils.getDbConnection()
    writeLog(componentName,infoLogLevel,"Created DB connection")
   
    writeLog(componentName,infoLogLevel,"Creating table in DB if not exists")
    databaseUtils.createTableIfNotExists(dbConnection,exportJobTableName,exportJobTableSchema)
    try:
        writeLog(componentName,infoLogLevel,"Generating access token")
        accessToken=generateAccessToken.getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
        print(accessToken)
        oauthToken=accessToken["accessToken"]

        columnsList=["jobId","RequestId","statusCheckCount"]
        writeLog(componentName,infoLogLevel,"Getting incomplete jobs from DB")
        jobsList=databaseUtils.getIncompleteJobs(dbConnection,exportJobTableName,IncompleteJobsReadCount,columnsList)
        writeLog(componentName,infoLogLevel,"Read "+str(len(jobsList))+" jobs")
        tasksList=[]
        for jobTuple in jobsList:
            jobId=jobTuple[0]
            requestId=jobTuple[1]
            statusCheckCount=jobTuple[2] if jobTuple[2] is not None else 0

            writeLog(componentName,infoLogLevel,"Creating async status check task for jobID: "+str(jobId))
            task=asyncio.create_task(getExportJobStatusUpdateTable(dbConnection,analyticsOrgId,analyticsServerUri,oauthToken,workspaceId,jobId,requestId,statusCheckCount))
            
            asyncio.sleep(0.5)
            tasksList.append(task)
        taskCount=0
        writeLog(componentName,infoLogLevel,"Created {0} async status check tasks".format(str(len(tasksList))))
        while(taskCount<len(tasksList)):
            for _ in range(exportJobStatusCheckConcurrentConnections):
                if(taskCount<len(tasksList)):
                    task=tasksList[taskCount]
                    writeLog(componentName,infoLogLevel,"Awaiting async status check task:{0}".format(str(taskCount)))
                    await task
                taskCount+=1

    except Exception as err:
        print("Error in data generation",err)
        writeLog(componentName,errorLogLevel,"Error in status check schedule:{0}".format(traceback.format_exc()))
    dbConnection.close()
    writeLog(componentName,infoLogLevel,"Schedule Ended")
    writeLog(componentName,infoLogLevel,"Awaiting async update tasks. Tasks created:{0}".format(len(asyncTasksList)))
    for t in asyncTasksList:
        await t


if __name__=="__main__":
    #global variables
    componentName="check status schedule"
    writeLog(componentName,infoLogLevel,"Schedule Started")
    asyncTasksList=[]
    asyncio.run(main())