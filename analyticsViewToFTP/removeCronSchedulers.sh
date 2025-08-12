pythonDir="/usr/local/bin/python3"
# pythonDir="/usr/bin/python3"
projectDir="/Users/adithiyan-14770/widgets/python_utils/analyticsViewToFTP/"
# projectDir="/home/sas/analyticsViewToFTP"
checkJobScheduleDir="${projectDir}checkJobStatus.py"
downloadJobScheduleDir="${projectDir}downloadExportJob.py"
SftpPushScheduleDir="${projectDir}pushFilesToSFTP.py"
getViewScheduleDir="${projectDir}getRequestsFromAnalytics.py"
filesCleanUpScheduleDir="${projectDir}logsFilesDeletionJob.py"

crontab -l | grep -v "${checkJobScheduleDir}" | head -1 | crontab -
crontab -l | grep -v "${downloadJobScheduleDir}" | head -1 | crontab -
crontab -l | grep -v "${SftpPushScheduleDir}" | head -1 | crontab -
crontab -l | grep -v "${getViewScheduleDir}" | head -1 | crontab -
crontab -l | grep -v "${filesCleanUpScheduleDir}" | head -1 | crontab -
