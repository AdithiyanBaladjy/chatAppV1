from oauthUtils import generateAccessToken
from dbUtils import databaseUtils
import requests
import urllib.parse
import json
import time
from datetime import datetime
import json
from projectConstants import zohoAccountsServerUri,clientId,clientSecret,code,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,analyticsOrgId,exportJobTableName, exportJobTableSchema, requestsReadLimit, inputTableWorkspaceName,inputTableViewName,inputTableOwnerMail
from loggingUtils import infoLogLevel,warningLogLevel,errorLogLevel, writeLog
from AnalyticsTableUtils_asyncio import getExportRequestsAnalyticsWithRetry,asyncUpdateAnalyticsTableWithRetry, asyncUpdateAnalyticsApiV1WithRetry
import asyncio
import traceback

#testing function
def getStoredResponse(fileName):
    apiResp=None
    with open(fileName,"r") as fp:
        apiResp=json.load(fp)
    return apiResp

#update analytics table row by request Id
def updateAnalyticsTable(analyticsOrgId,analyticsServerUri,accessToken,workspaceId,viewId,requestId,updateDict):
    configJson={}
    configJson["columns"]=updateDict
    configJson["criteria"]="\"SFTP_export_requests\".\"requestId\"='{0}'".format(requestId)
    
    encodedConfigJson=urllib.parse.quote_plus(configJson)
    updateUrl="https://"+analyticsServerUri+"/restapi/v2/workspaces/"+workspaceId+"/views/"+viewId+"/rows?CONFIG="+encodedConfigJson
    apiHeader={"ZANALYTICS-ORGID":analyticsOrgId,"Authorization":"Zoho-oauthtoken "+accessToken}
    try:
        apiResp=requests.put(updateUrl,headers=apiHeader)
    except requests.exceptions.HTTPError as errh:
        #Http error
        writeLog(componentName,errorLogLevel,"HTTP error in calling export API: "+str(errh))
        
    except requests.exceptions.ConnectionError as errc:
        #Connection error
        writeLog(componentName,errorLogLevel,"Connection error in calling export API: "+str(errc))
        
    except requests.exceptions.Timeout as errt:
        writeLog(componentName,errorLogLevel,"Time-out error in calling export API: "+str(errt))
        #Time-out error
        
    except requests.exceptions.RequestException as err:
        #Generic error
        writeLog(componentName,errorLogLevel,"Error in calling export API: "+str(err))
        
    writeLog(componentName,infoLogLevel,"Analytics API response received: "+apiResp.text)
    try:
        writeLog(componentName,infoLogLevel,"Parsing API response received")
        apiRespDict=json.loads(apiResp.text)
        return apiRespDict
    except Exception as e:
        writeLog(componentName,errorLogLevel,"Error in converting export view response to json/reading response. API response: "+json.dumps(apiResp))
        # raise Exception("Error in converting export view response to json/reading response"+e)


#Creates a bulk export job request
#can raise exception
def initiateBulkExportView(analyticsOrgId,analyticsServerUri,accessToken,workspaceId,viewId):
    writeLog(componentName,infoLogLevel,"Getting access token.")
    oauthToken=generateAccessToken.getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
    accessToken=oauthToken["accessToken"]
    configJson={"responseFormat":"csv"}
    configJsonUrlEncoded=urllib.parse.quote_plus(str(configJson))
    exportViewUrl="https://"+analyticsServerUri+"/restapi/v2/bulk/workspaces/"+workspaceId+"/views/"+viewId+"/data?CONFIG="+str(configJsonUrlEncoded)
    apiHeader={"ZANALYTICS-ORGID":analyticsOrgId,"Authorization":"Zoho-oauthtoken "+accessToken}
    try:
        apiResp=requests.get(exportViewUrl,headers=apiHeader)
    except requests.exceptions.HTTPError as errh:
        #Http error
        writeLog(componentName,errorLogLevel,"HTTP error in calling export API: "+str(errh))
        
    except requests.exceptions.ConnectionError as errc:
        #Connection error
        writeLog(componentName,errorLogLevel,"Connection error in calling export API: "+str(errc))
        
    except requests.exceptions.Timeout as errt:
        writeLog(componentName,errorLogLevel,"Time-out error in calling export API: "+str(errt))
        #Time-out error
        
    except requests.exceptions.RequestException as err:
        #Generic error
        writeLog(componentName,errorLogLevel,"Error in calling export API: "+str(err))
        
    writeLog(componentName,infoLogLevel,"Analytics API response received")
    try:
        writeLog(componentName,infoLogLevel,"Parsing API response received")
        apiRespDict=json.loads(apiResp.text)
        return apiRespDict
    except Exception as e:
        writeLog(componentName,errorLogLevel,"Error in converting export view response to json/reading response. API response: "+json.dumps(apiResp))
        # raise Exception("Error in converting export view response to json/reading response"+e)

async def main():
    asyncTasks=[]
    writeLog(componentName,infoLogLevel,"get Requests Schedule Started")
    dbConnection=databaseUtils.getDbConnection()
    writeLog(componentName,infoLogLevel,"Created DB connection")
    writeLog(componentName,infoLogLevel,"Creating table if not exists")
    databaseUtils.createTableIfNotExists(dbConnection,exportJobTableName,exportJobTableSchema)
    try:
        writeLog(componentName,infoLogLevel,"Generating access token")
        accessToken=generateAccessToken.getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
        print(accessToken)
        oauthToken=accessToken["accessToken"]
        writeLog(componentName,infoLogLevel,"Calling Analytics Export API.")
        exportViewResp=getExportRequestsAnalyticsWithRetry(componentName,analyticsOrgId,analyticsServerUri,accessToken,inputTableWorkspaceName,inputTableViewName,inputTableOwnerMail)
        if(exportViewResp["status"]=="success"):
            #check data key in the response and initiate bulk export views - db updates 
            #Then update the analytics table back with rowId
            exportViewKeys=exportViewResp.keys()
            if("data" in exportViewKeys):
                #API success response
                for dataRow in exportViewResp["data"]:
                    exportViewId=dataRow["viewId"]
                    exportWorkspaceId=dataRow["workspaceId"]
                    exportRequestId=dataRow["requestId"]
                    #initiate export job request for this view ID
                    #on success store the requestId in embeddedDB & write back to analytics table
                    #as requestStatus as "Request Queued"
                    writeLog(componentName,infoLogLevel,"Initiating bulk export view for the view ID:{0}".format(exportViewId))
                    bulkResponse=initiateBulkExportView(analyticsOrgId,analyticsServerUri,oauthToken,exportWorkspaceId,exportViewId)
                    analyticsRespKeys=bulkResponse.keys()
                    writeLog(componentName,infoLogLevel,"Checking response status")
                    if (("status" in analyticsRespKeys) and ("data" in analyticsRespKeys)):
                        #check if status is success 
                        if(bulkResponse["status"]=="success"):
                            #create a export job entry in exportJobs table
                            writeLog(componentName,infoLogLevel,"API Success")
                            apiData=bulkResponse["data"]
                            dataKeys=apiData.keys()
                            if("jobId" not in dataKeys):
                                #write error log and continue with next view ID
                                writeLog(componentName,errorLogLevel,"Error in export API Response for view Id:{0}. Analytics Response:{1}".format(exportViewId,json.dumps(bulkResponse)))
                                continue

                            jobId=bulkResponse["data"]["jobId"]
                            if (jobId != "") and (jobId is not None):
                                currentTimeInSecs=time.time()
                                currentDateTimeStr=datetime.now().strftime("%d-%m-%YT%H:%M:%S")
                                RowToInsert=[{"columnName":"jobId","value":jobId},{"columnName":"viewId","value":exportViewId},
                                {"columnName":"createdTimeReal","value":currentTimeInSecs}, {"columnName":"createdTimeInText","value":currentDateTimeStr}, {"columnName":"pushedToSFTP","value":0},{"columnName":"RequestId","value":exportRequestId}
                                ]

                                writeLog(componentName,infoLogLevel,"Inserting row into DB")
                                pushedRowId=databaseUtils.insertRowWithNamedColumns(dbConnection,exportJobTableName,exportJobTableSchema,RowToInsert)
                                writeLog(componentName,infoLogLevel,"Created export job in DB")
                                print("pushed row into database",pushedRowId)
                                writeLog(componentName,infoLogLevel,"Updated request status in analytics input table")
                                #do this in a separate process with 3 retries over 3 minutes
                                # resp=asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,InputTableWorkspaceId,InputTableViewId,exportRequestId,{"RequestStatus":"Request queued","dbRowId":str(pushedRowId)})
                                currentTime=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                rowUpdateDict={"RequestStatus":"Request queued","dbRowId":str(pushedRowId),"jobId":jobId,"jobCreatedDateTime":currentTime}
                                updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,exportRequestId,rowUpdateDict,"dd/MM/yyyy HH:mm:ss")
                                asyncTasks.append(updateTask)
                        elif(bulkResponse["status"]=="failure"):   
                            writeLog(componentName,errorLogLevel,"Bulk export request failed with response:{0}".format(bulkResponse))
                            #do this in a separate process with 3 retries over 3 minutes
                            # resp=asyncUpdateAnalyticsTableWithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,InputTableWorkspaceId,InputTableViewId,exportRequestId,{"RequestStatus":"Export request failure"})
                            updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,exportRequestId,{"RequestStatus":"Export request failure","jobCreationErrorLog":json.dumps(bulkResponse)})
                            asyncTasks.append(updateTask)
                        else:
                        #if status is failure raise Exception with the response object
                            writeLog(componentName,errorLogLevel,"Error in export API"+json.dumps(bulkResponse))
                            print("Error in export view API",bulkResponse)
                            updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,exportRequestId,{"RequestStatus":"Export request failure","jobCreationErrorLog":json.dumps(bulkResponse)})
                            asyncTasks.append(updateTask)
                    else:
                        #Response is not in expected format
                        writeLog(componentName,errorLogLevel,"Error in bulk export API Response for view Id:{0}. Analytics Response:{1}".format(exportViewId,json.dumps(bulkResponse)))
                        updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,exportRequestId,{"RequestStatus":"Export request failure","jobCreationErrorLog":json.dumps(bulkResponse)})
                        asyncTasks.append(updateTask)
            else:
                #API response in unexpected format
                writeLog(componentName,errorLogLevel,"Fetch requests response unexpected:{0}".format(exportViewResp))
                updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,exportRequestId,{"RequestStatus":"Export request failure","jobCreationErrorLog":"Unexpected response - "+json.dumps(bulkResponse)})
                asyncTasks.append(updateTask)      
        elif(exportViewResp["status"]=="failure"):
            #write log and exit
            writeLog(componentName,errorLogLevel,"Fetch requests response failed:{0}".format(exportViewResp))
        elif(exportViewResp["status"]=="failed after retries"):
            #write log and exit
            writeLog(componentName,errorLogLevel,"Fetch requests failed after multiple retries failed:{0}".format(exportViewResp))
        
    except Exception as err:
        writeLog(componentName,errorLogLevel,"Requests read schedule failed. Error: "+traceback.format_exc())
    dbConnection.close()
    writeLog(componentName,infoLogLevel,"Requests read schedule ended")
    writeLog(componentName,infoLogLevel,"Awaiting for async tasks to get completed. Tasks created:{0}".format(len(asyncTasks)))
    for t in asyncTasks:
        await t
    pass



if __name__=="__main__":
    #global variables
    componentName="get requests Schedule"
    asyncio.run(main())
    
    """
    accessToken=generateAccessToken.getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
    print(accessToken)
    oauthToken=accessToken["accessToken"]
    currentTime=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    rowUpdateDict={"RequestStatus":"Request queued","dbRowId":str(1),"jobId":1,"jobCreatedDateTime":currentTime}
    updateTask=asyncUpdateAnalyticsApiV1WithRetry(componentName,analyticsOrgId,analyticsServerUri,oauthToken,inputTableOwnerMail,inputTableWorkspaceName,inputTableViewName,"1",rowUpdateDict)
    asyncio.run(updateTask) """