import paramiko
from projectConstants import sftpDirectory,outputFilesDirectory,sftpServerIp,sftpUserName,sftpPassword
import os
import traceback

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
        print("Exception in connecting via SSH",excp)
        return
    try:
        sftpClient=sshClient.open_sftp()
        sftpClient.chdir(sftpDirectory)
        localFile=open(outputFilesDirectory+fileName,mode='r')
        chunkInd=1
        with sftpClient.file(fileName,mode='w',bufsize=10000000) as remoteFile:
            for fileChunk in readInChunks(localFile,10000000):
                remoteFile.write(fileChunk)
                print("written file chunk",chunkInd)
                chunkInd+=1
        localFile.close()

    except Exception as ex:
        #Raise error: SFTP connection failed
        print("SFTP connection failure",traceback.format_exc())
    finally:
        sshClient.close()

if __name__=="__main__":
    pushFileToSftpInChunks(sftpServerIp,sftpUserName,sftpPassword,"100068000003499894_29_08_2024_15_37_00.csv")