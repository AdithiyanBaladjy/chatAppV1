crontab -l > mycron
pythonDir="/usr/local/bin/python3"
# pythonDir="/usr/bin/python3"
projectDir="/Users/adithiyan-14770/widgets/python_utils/analyticsViewToFTP/"
# projectDir="/home/sas/analyticsViewToFTP"
checkJobScheduleDir="${projectDir}checkJobStatus.py"
downloadJobScheduleDir="${projectDir}downloadExportJob.py"
SftpPushScheduleDir="${projectDir}pushFilesToSFTP.py"
getViewScheduleDir="${projectDir}getRequestsFromAnalytics.py"
filesCleanUpScheduleDir="${projectDir}logsFilesDeletionJob.py"

checkJobScheduleFrequency="*" #every minute
downloadJobScheduleFrequency="*" #every minute
sftpPushScheduleFrequency="*/2" #every two minutes
getViewScheduleFrequency="*/2" #every two minutes
filesCleanUpFrequency="* 18 * * *" #Everyday at 6:00 PM

echo "${checkJobScheduleFrequency} * * * * ${pythonDir} ${checkJobScheduleDir}" >> mycron
echo "${downloadJobScheduleFrequency} * * * * ${pythonDir} ${downloadJobScheduleDir}" >> mycron
echo "${sftpPushScheduleFrequency} * * * * ${pythonDir} ${SftpPushScheduleDir}" >> mycron
echo "${sftpPushScheduleFrequency} * * * * ${pythonDir} ${getViewScheduleDir}" >> mycron
echo "${filesCleanUpFrequency} ${pythonDir} ${filesCleanUpScheduleDir}" >> mycron

crontab mycron
rm mycron