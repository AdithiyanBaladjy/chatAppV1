from oauthUtils import generateAccessToken
from dbUtils import databaseUtils
import requests
import urllib.parse
import json
import time
from datetime import datetime
import json
from projectConstants import zohoAccountsServerUri,clientId,clientSecret,code,analyticsServerUri,workspaceId,viewsList,analyticsOrgId,exportJobTableName, exportJobTableSchema
from loggingUtils import writeLogAsync,infoLogLevel,warningLogLevel,errorLogLevel
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
    try:
        apiResp=requests.get(exportViewUrl,headers=apiHeader)
    except requests.exceptions.HTTPError as errh:
        #Http error
        writeLogAsync(componentName,errorLogLevel,"HTTP error in calling export API: "+str(errh))
        
    except requests.exceptions.ConnectionError as errc:
        #Connection error
        writeLogAsync(componentName,errorLogLevel,"Connection error in calling export API: "+str(errc))
        
    except requests.exceptions.Timeout as errt:
        writeLogAsync(componentName,errorLogLevel,"Time-out error in calling export API: "+str(errt))
        #Time-out error
        
    except requests.exceptions.RequestException as err:
        #Generic error
        writeLogAsync(componentName,errorLogLevel,"Error in calling export API: "+str(err))
        
    writeLogAsync(componentName,infoLogLevel,"Analytics API response received")
    try:
        writeLogAsync(componentName,infoLogLevel,"Parsing API response received")
        apiRespDict=json.loads(apiResp.text)
        return apiRespDict
    except Exception as e:
        writeLogAsync(componentName,errorLogLevel,"Error in converting export view response to json/reading response. API response: "+json.dumps(apiResp))
        # raise Exception("Error in converting export view response to json/reading response"+e)

def main():
   
    writeLogAsync(componentName,infoLogLevel,"Trigger Started")
    dbConnection=databaseUtils.getDbConnection()
    writeLogAsync(componentName,infoLogLevel,"Created DB connection")
    writeLogAsync(componentName,infoLogLevel,"Creating table if not exists")
    databaseUtils.createTableIfNotExists(dbConnection,exportJobTableName,exportJobTableSchema)
    try:
        writeLogAsync(componentName,infoLogLevel,"Generating access token")
        accessToken=generateAccessToken.getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
        print(accessToken)
        oauthToken=accessToken["accessToken"]

        writeLogAsync(componentName,infoLogLevel,"Calling Analytics Export API. Input views length:{0}".format(len(viewsList)))
        for viewIId in viewsList:
            exportViewResp=getAnalyticsView(analyticsOrgId,analyticsServerUri,oauthToken,workspaceId,viewIId)
            # exportViewResp=getStoredResponse("exportApiResp.json")
            #continue from here
            analyticsRespKeys=exportViewResp.keys()
            writeLogAsync(componentName,infoLogLevel,"Checking response status")
            if (("status" in analyticsRespKeys) and ("data" in analyticsRespKeys)):
                #check if status is success 
                if(exportViewResp["status"]=="success"):
                    #create a export job entry in exportJobs table
                    writeLogAsync(componentName,infoLogLevel,"API Success")
                    apiData=exportViewResp["data"]
                    dataKeys=apiData.keys()
                    if("jobId" not in dataKeys):
                        #write error log and continue with next view ID
                        writeLogAsync(componentName,errorLogLevel,"Error in export API Response for view Id:{0}. Analytics Response:{1}".format(viewIId,json.dumps(exportViewResp)))
                        continue
                        
                    jobId=exportViewResp["data"]["jobId"]
                    if (jobId != "") and (jobId is not None):
                        currentTimeInSecs=time.time()
                        currentDateTimeStr=datetime.now().strftime("%d-%m-%YT%H:%M:%S")
                        RowToInsert=[{"columnName":"jobId","value":jobId},{"columnName":"viewId","value":viewIId},
                        {"columnName":"createdTimeReal","value":currentTimeInSecs}, {"columnName":"createdTimeInText","value":currentDateTimeStr}, {"columnName":"pushedToSFTP","value":0}
                        ]

                        writeLogAsync(componentName,infoLogLevel,"Inserting row into DB")
                        pushedRowId=databaseUtils.insertRowWithNamedColumns(dbConnection,exportJobTableName,exportJobTableSchema,RowToInsert)
                        writeLogAsync(componentName,infoLogLevel,"Created export job in DB")
                        print("pushed row into database",pushedRowId)
                else:
                #if status is failure raise Exception with the response object
                    writeLogAsync(componentName,errorLogLevel,"Error in export API"+json.dumps(exportViewResp))
                    print("Error in export view API",exportViewResp)
            else:
                #Response is not in expected format
                writeLogAsync(componentName,errorLogLevel,"Error in export API Response for view Id:{0}. Analytics Response:{1}".format(viewIId,json.dumps(exportViewResp)))
                

    except Exception as err:
        writeLogAsync(componentName,errorLogLevel,"Creating view export job failed. Error"+traceback.format_exc())
        print("Error in data generation",err)
    dbConnection.close()
    writeLogAsync(componentName,infoLogLevel,"View trigger ended")
if __name__=="__main__":
    #global variables
    componentName="get view trigger"
    main()