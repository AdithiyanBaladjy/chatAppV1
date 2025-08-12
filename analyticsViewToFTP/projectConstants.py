isUatInstance=False #To be set False for production release
zohoAccountsServerUri="ucrmlogin.unionbankofindia.co.in"
clientId="1000.K2ZGTGIFRY9IZG9QXO788WALVRTWON"
clientSecret="29eecf0bb3ab5044272ea4c4d33e54a59d40ec233e"
code="1000.af92278f3e364ef2b070dc52041b741c.6041fd48ecea108101e1c239edacf45c" #read & update
analyticsServerUri="analytics.unionbankofindia.co.in"
# workspaceId="100068000000003252"
workspaceId="100068000000003252"
inputTableWorkspaceName="Desk_ccudesk"
inputTableViewName="SFTP_export_requests"
inputTableOwnerMail="crmadmin1@unionbankofindia.bank"
InputTableWorkspaceId="100068000000029015"
InputTableViewId="100068000003344940"
# viewId="100068000001023984"
# viewId="100068000000003256"
# viewsList=["100068000000003256","100068000001657790","100068000000204585"]
viewsList=[]
analyticsOrgId="11606"
exportJobTableName="ExportJobsStatus"

exportJobTableSchema=[{"columnName":"rowId","columnType":"INTEGER","primaryKey":True},{"columnName":"jobId","columnType":"INTEGER"},{"columnName":"jobStatus","columnType":"text"},{"columnName":"failureLog","columnType":"text"},{"columnName":"viewId","columnType":"INTEGER"},
    {"columnName":"createdTimeReal","columnType":"real"},{"columnName":"createdTimeInText","columnType":"text"},{"columnName":"jobCompletedTimeReal","columnType":"real"},
    {"columnName":"jobCompletedTimeInText","columnType":"text"},{"columnName":"pushedToSFTP","columnType":"INTEGER"},
    {"columnName":"SFTPPushTimeReal","columnType":"real"},{"columnName":"SFTPPushTimeInText","columnType":"text"},{"columnName":"underProcess","columnType":"INTEGER"},{"columnName":"downloadUrl","columnType":"text"},{"columnName":"downloadExpiryTime","columnType":"real"},
    {"columnName":"localFileName","columnType":"text"},{"columnName":"RequestId","columnType":"text"},{"columnName":"statusCheckCount","columnType":"INTEGER"},{"columnName":"downloadTryCount","columnType":"INTEGER"},{"columnName":"sftpPushCount","columnType":"INTEGER"}
    ]
projectDir=""
sftpServerIp=""
sftpUserName=""
sftpPassword=""
sftpDirectory=""
#File Export Deletion related variables
fileExportsDir=""
logsDir=""
if(isUatInstance==True):
    projectDir="/Users/adithiyan-14770/widgets/python_utils/analyticsViewToFTP/"
    sftpServerIp="172.23.125.103"
    sftpUserName="sftp_user"
    sftpPassword="changeme"
    sftpDirectory="sftp_user/analyticsExport/"
    
else:
    projectDir="/home/sas/analyticsViewToFTP/"
    sftpServerIp=None
    sftpUserName=""
    sftpPassword=""
    sftpDirectory=""

outputFilesDirectory=projectDir+"FileExports/"



IncompleteJobsReadCount=50
completedJobsReadCount=50

sftpConcurrentConnectionsCount=4
exportJobStatusCheckConcurrentConnections=50
fileDownloadConcurrencyLimit=50
requestsReadLimit=50

#retry limits
statusCheckRetryLimit=60
downloadRetryLimit=60
sftpRetryLimit=30

#File clean-up schedule variables
fileExportsDir=projectDir+"FileExports/"
logsDir=projectDir+"logs/"
fileCleanUpDays=2
fileCleanUpLimitInSecs=fileCleanUpDays*24*60*60

logCleanUpDays=90
logCleanUpLimitInSecs=logCleanUpDays*24*60*60





