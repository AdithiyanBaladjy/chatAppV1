from oauthUtils import generateAccessToken
from dbUtils import databaseUtils
import requests
import urllib.parse
import json
import time
from datetime import datetime
import json
from projectConstants import zohoAccountsServerUri,clientId,clientSecret,code,analyticsServerUri,InputTableWorkspaceId,InputTableViewId,analyticsOrgId,exportJobTableName, exportJobTableSchema, requestsReadLimit, inputTableWorkspaceName,inputTableViewName,inputTableOwnerMail
from loggingUtils import writeLog,infoLogLevel,warningLogLevel,errorLogLevel
import multiprocessing as mp
import ast

retryTimeOut=1 #1 second
nRetries=3 #3 retry

#update analytics table row by request Id V1
def updateAnalyticsTableV1(callingComponent,analyticsOrgId,analyticsServerUri,accessToken,ownerEmail,workspaceName,tableName,requestId,updateDict):
    configJson={}
    configJson["ZOHO_ACTION"]="UPDATE"
    configJson["ZOHO_OUTPUT_FORMAT"]="JSON"
    configJson["ZOHO_ERROR_FORMAT"]="JSON"
    configJson["ZOHO_API_VERSION"]="1.0"
    updateKeys=updateDict.keys()
    for key in updateKeys:
        configJson[key]=updateDict[key]
    configJson["ZOHO_CRITERIA"]="(\"requestId\"='{0}')".format(requestId)

    ownerEmailEncoded=urllib.parse.quote_plus(json.dumps(ownerEmail),safe="\"")
    workspaceEncoded=urllib.parse.quote_plus(json.dumps(workspaceName),safe="\"")
    tableNameEncoded=urllib.parse.quote_plus(json.dumps(tableName),safe="\"")

    ownerEmailEncoded=ownerEmailEncoded.replace("\"","")
    workspaceEncoded=workspaceEncoded.replace("\"","")
    tableNameEncoded=tableNameEncoded.replace("\"","")

    updateUrl="https://"+analyticsServerUri+"/api/"+ownerEmailEncoded+"/"+workspaceEncoded+"/"+tableNameEncoded
    
    apiHeader={"ZANALYTICS-ORGID":analyticsOrgId,"Authorization":"Zoho-oauthtoken "+accessToken}
    apiRespDecoded=None
    try:
        apiResp=requests.post(updateUrl,headers=apiHeader,data=configJson)
        
    except requests.exceptions.HTTPError as errh:
        #Http error
        writeLog(callingComponent,errorLogLevel,"HTTP error in calling export API: "+str(errh))
        return {"status":"network error","errorDetails":errh}
    except requests.exceptions.ConnectionError as errc:
        #Connection error
        writeLog(callingComponent,errorLogLevel,"Connection error in calling export API: "+str(errc))
        return {"status":"network error","errorDetails":errc}
    except requests.exceptions.Timeout as errt:
        writeLog(callingComponent,errorLogLevel,"Time-out error in calling export API: "+str(errt))
        return {"status":"network error","errorDetails":errt}
        #Time-out error
        
    except requests.exceptions.RequestException as err:
        #Generic error
        writeLog(callingComponent,errorLogLevel,"Error in calling export API: "+str(err))
        return {"status":"network error","errorDetails":err}

    writeLog(callingComponent,infoLogLevel,"Analytics API response received: "+apiResp.text)
    try:
        writeLog(callingComponent,infoLogLevel,"Parsing API response received")
        apiRespDecoded=ast.literal_eval(apiResp.content.decode("UTF-8"))
        return apiRespDecoded
    except Exception as e:
        writeLog(callingComponent,errorLogLevel,"Error in converting export view response to json/reading response. API response: "+json.dumps(apiResp))
        return {"status":"network error","errorDetails":e}

#V1 update API retry
def updateAnalyticsApiV1WithRetry(callingComponent,analyticsOrgId,analyticsServerUri,accessToken,ownerEmail,workspaceName,tableName,requestId,updateDict):
    for _ in range(nRetries):
        writeLog(callingComponent,infoLogLevel,"Getting access token.")
        accessToken=generateAccessToken.getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
        writeLog(callingComponent,infoLogLevel,"Getting access token.")
        oauthToken=accessToken["accessToken"]
        writeLog(callingComponent,infoLogLevel,"Trying to update Analytics input table. Trial:{0}".format(_+1))
        apiResp=updateAnalyticsTableV1(callingComponent,analyticsOrgId,analyticsServerUri,oauthToken,ownerEmail,workspaceName,tableName,requestId,updateDict)
        writeLog(callingComponent,infoLogLevel,"Checking for status in update response")
        apiResponseCont=apiResp["response"]
        apiResponseKeys=apiResponseCont
        if("result" in apiResponseKeys):
            writeLog(callingComponent,infoLogLevel,"Analytics table update success") 
            break                          
        elif("error" in apiResponseKeys):
            writeLog(callingComponent,errorLogLevel,"Analytics table update failure. Response: "+json.dumps(apiResp))
            break
        elif(apiResp["status"]=="network failure"):
            writeLog(callingComponent,errorLogLevel,"Network disturbance / failed to reach analytics server. Retrying analytics update in {0} seconds".format(retryTimeOut))
            time.sleep(retryTimeOut)

def asyncUpdateAnalyticsApiV1WithRetry(callingComponent,analyticsOrgId,analyticsServerUri,accessToken,ownerEmail,workspaceName,tableName,requestId,updateDict):
    updateProcess=mp.Process(target=updateAnalyticsApiV1WithRetry,args=(callingComponent,analyticsOrgId,analyticsServerUri,accessToken,ownerEmail,workspaceName,tableName,requestId,updateDict))
    updateProcess.start()

#update analytics table row by request Id
def updateAnalyticsTable(callingComponent,analyticsOrgId,analyticsServerUri,accessToken,workspaceId,viewId,requestId,updateDict,dateFormat):
    configJson={}
    configJson["columns"]=updateDict
    configJson["criteria"]="\"SFTP_export_requests\".\"requestId\"='{0}'".format(requestId)
    if(dateFormat is not None):
        configJson["dateFormat"]=dateFormat
    encodedConfigJson=urllib.parse.quote_plus(json.dumps(configJson))
    updateUrl="https://"+analyticsServerUri+"/restapi/v2/workspaces/"+workspaceId+"/views/"+viewId+"/rows?CONFIG="+encodedConfigJson
    apiHeader={"ZANALYTICS-ORGID":analyticsOrgId,"Authorization":"Zoho-oauthtoken "+accessToken}
    try:
        apiResp=requests.put(updateUrl,headers=apiHeader)
    except requests.exceptions.HTTPError as errh:
        #Http error
        writeLog(callingComponent,errorLogLevel,"HTTP error in calling export API: "+str(errh))
        return {"status":"network error","errorDetails":errh}
    except requests.exceptions.ConnectionError as errc:
        #Connection error
        writeLog(callingComponent,errorLogLevel,"Connection error in calling export API: "+str(errc))
        return {"status":"network error","errorDetails":errc}
    except requests.exceptions.Timeout as errt:
        writeLog(callingComponent,errorLogLevel,"Time-out error in calling export API: "+str(errt))
        return {"status":"network error","errorDetails":errt}
        #Time-out error
        
    except requests.exceptions.RequestException as err:
        #Generic error
        writeLog(callingComponent,errorLogLevel,"Error in calling export API: "+str(err))
        return {"status":"network error","errorDetails":err}

    writeLog(callingComponent,infoLogLevel,"Analytics API response received: "+apiResp.text)
    try:
        writeLog(callingComponent,infoLogLevel,"Parsing API response received")
        apiRespDict=json.loads(apiResp.text)
        return apiRespDict
    except Exception as e:
        writeLog(callingComponent,errorLogLevel,"Error in converting export view response to json/reading response. API response: "+json.dumps(apiResp))
        return {"status":"network error","errorDetails":e}
        

def updateAnalyticsTableWithRetry(callingComponent,analyticsOrgId,analyticsServerUri,workspaceId,viewId,requestId,updateDict,dateFormat):
    for _ in range(nRetries):
        writeLog(callingComponent,infoLogLevel,"Getting access token.")
        accessToken=generateAccessToken.getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
        writeLog(callingComponent,infoLogLevel,"Getting access token.")
        oauthToken=accessToken["accessToken"]
        writeLog(callingComponent,infoLogLevel,"Trying to update Analytics input table. Trial:{0}".format(_+1))
        apiResp=updateAnalyticsTable(callingComponent,analyticsOrgId,analyticsServerUri,oauthToken,workspaceId,viewId,requestId,updateDict,dateFormat)
        writeLog(callingComponent,infoLogLevel,"Checking for status in update response")
        if(apiResp["status"]=="success"):
            writeLog(callingComponent,infoLogLevel,"Analytics table update success") 
            break                          
        elif(apiResp["status"]=="failure"):
            writeLog(callingComponent,errorLogLevel,"Analytics table update failure. Response: "+json.dumps(apiResp))
            break
        elif(apiResp["status"]=="network failure"):
            writeLog(callingComponent,errorLogLevel,"Network disturbance / failed to reach analytics server. Retrying analytics update in {0} seconds".format(retryTimeOut))
            time.sleep(retryTimeOut)

def asyncUpdateAnalyticsTableWithRetry(callingComponent,analyticsOrgId,analyticsServerUri,workspaceId,viewId,requestId,updateDict,dateFormat=None):
    updateProcess=mp.Process(target=updateAnalyticsTableWithRetry,args=(callingComponent,analyticsOrgId,analyticsServerUri,workspaceId,viewId,requestId,updateDict,dateFormat))
    updateProcess.start()
    updateProcess.join()

#Gets export requests created in analytics input table
def getExportRequestsAnalytics(callingComponent,analyticsOrgId,analyticsServerUri,accessToken,inputTableWorkspaceName,inputTableViewName,inputTableOwnerMail):
    configJson={"ZOHO_ACTION":"EXPORT","ZOHO_OUTPUT_FORMAT":"JSON","ZOHO_ERROR_FORMAT":"JSON","ZOHO_API_VERSION":"1.0","ZOHO_SQLQUERY":"select * from `SFTP_export_requests` where `RequestStatus` is NULL","KEY_VALUE_FORMAT":"true"}
    ownerMail=urllib.parse.quote_plus(inputTableOwnerMail)
    workspaceName=urllib.parse.quote_plus(inputTableWorkspaceName)
    tableViewName=urllib.parse.quote_plus(inputTableViewName)
    exportViewUrl="https://"+analyticsServerUri+"/api/"+ownerMail+"/"+workspaceName+"/"+tableViewName
    apiHeader={"ZANALYTICS-ORGID":analyticsOrgId,"Authorization":"Zoho-oauthtoken "+accessToken}
    try:
        apiResp=requests.post(exportViewUrl,headers=apiHeader,data=configJson)
    except requests.exceptions.HTTPError as errh:
        #Http error
        writeLog(callingComponent,errorLogLevel,"HTTP error in calling export API: "+str(errh))
        return {"status":"network failure"}
    except requests.exceptions.ConnectionError as errc:
        #Connection error
        writeLog(callingComponent,errorLogLevel,"Connection error in calling export API: "+str(errc))
        return {"status":"network failure"}
    except requests.exceptions.Timeout as errt:
        writeLog(callingComponent,errorLogLevel,"Time-out error in calling export API: "+str(errt))
        #Time-out error
        return {"status":"network failure"}
    except requests.exceptions.RequestException as err:
        #Generic error
        writeLog(callingComponent,errorLogLevel,"Error in calling export API: "+str(err))
        return {"status":"network failure"}
    writeLog(callingComponent,infoLogLevel,"Analytics API response received: "+apiResp.text)
    try:
        writeLog(callingComponent,infoLogLevel,"Parsing API response received")
        apiRespDict=json.loads(apiResp.text)
        return apiRespDict
    except Exception as e:
        writeLog(callingComponent,errorLogLevel,"Error in converting export view response to json/reading response. API response: "+json.dumps(apiResp))
        # raise Exception("Error in converting export view response to json/reading response"+e)
        return {"status":"network failure"}

#fetch export requests from analytics with retries for network failure
def getExportRequestsAnalyticsWithRetry(callingComponent,analyticsOrgId,analyticsServerUri,accessToken,inputTableWorkspaceName,inputTableViewName,inputTableOwnerMail):
    for _ in range(nRetries):
        writeLog(callingComponent,infoLogLevel,"Getting access token.")
        accessToken=generateAccessToken.getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
        oauthToken=accessToken["accessToken"]
        writeLog(callingComponent,infoLogLevel,"Trying to read export requests from Analytics input table. Trial:{0}".format(_+1))
        apiResp=getExportRequestsAnalytics(callingComponent,analyticsOrgId,analyticsServerUri,oauthToken,inputTableWorkspaceName,inputTableViewName,inputTableOwnerMail)
        writeLog(callingComponent,infoLogLevel,"Checking for status in fetch response")
        if("data" in apiResp.keys()):
            apiResp["status"]="success"
        else:
            apiResp["status"]="failure"
        if(apiResp["status"]=="success"):
            writeLog(callingComponent,infoLogLevel,"Export requests fetch success") 
            return apiResp                          
        elif(apiResp["status"]=="failure"):
            writeLog(callingComponent,errorLogLevel,"Export requests fetch failure. Response: "+json.dumps(apiResp))
            return apiResp
        elif(apiResp["status"]=="network failure"):
            writeLog(callingComponent,errorLogLevel,"Network disturbance / failed to reach analytics server. Retrying export request in {0} seconds".format(retryTimeOut))
            time.sleep(retryTimeOut)
    return {"status":"failed after retries","details":"maximum retries exhausted"}
            

if __name__=="__main__":
    updateDict={"RequestStatus":"test Request queued","dbRowId":"1"}
    updateAnalyticsApiV1WithRetry("Test",analyticsOrgId,analyticsServerUri,None,"crmadmin1@unionbankofindia.bank","Desk_ccudesk","SFTP_export_requests","1",updateDict)