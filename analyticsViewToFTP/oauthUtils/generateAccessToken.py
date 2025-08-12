import requests
import json
import time
from projectConstants import projectDir,isUatInstance
from encrDecrUtils import aesDecryptStr, aesEncryptStr

#output on success could be of the form
#{
# "access_token":<token String>,
# "refresh_token":<refresh token string>,
# "scope":<scope>,
# "token_type":"Bearer",
#"expires_in":3600
# }

packageHD="./oauthUtils/"
packageHD="/Users/adithiyan-14770/widgets/python_utils/analyticsViewToFTP/oauthUtils/"
if(isUatInstance!=True):
    packageHD=projectDir+"oauthUtils/"
def generateAccessTokenFromCode(accountsServerUri,clientId,clientSecret,code):
    accessTokenUrl="https://"+accountsServerUri+"/oauth/v2/token?code="+code+"&client_id="+clientId+"&client_secret="+clientSecret+"&grant_type=authorization_code"
    try:
        tokenResponse=requests.post(accessTokenUrl)
        responseDict=json.loads(tokenResponse.text)
        print(tokenResponse.text)
        if 'error' in responseDict.keys():
            raise Exception("Error in authentication"+tokenResponse.text)
        return responseDict
    except requests.exceptions.RequestException as e:
        print("Request Exception occurred while hitting access token API",e)
        raise Exception("Error in generating access token from code: "+str(e))
        
    except Exception as e:
        print("Error in calling access token generation API",e)
        raise Exception("Error in generating access token from code: "+str(e))
        

def RefreshAccessToken(accountsServerUri,refreshToken,clientId,clientSecret,redirectUri):
    accessTokenUrl="https://"+accountsServerUri+"/oauth/v2/token"
    reqParam={}
    reqParam["refresh_token"]=refreshToken
    reqParam["client_id"]=clientId
    reqParam["client_secret"]=clientSecret
    if(redirectUri is not None):
        reqParam["redirect_Uri"]=redirectUri
    reqParam["grant_type"]="refresh_token"
    try:
        tokenResponse=requests.post(accessTokenUrl,data=reqParam)
        responseDict=json.loads(tokenResponse.text)
        print(tokenResponse.text)
        if 'error' in responseDict.keys():
            raise Exception("Error in refreshing access token"+tokenResponse.text)
        return responseDict
    except requests.exceptions.RequestException as e:
        print("Request Exception occurred while hitting refresh access token API",e)
        raise Exception("Error in refreshing access token"+str(e))
        
    except Exception as e:
        print("Error in calling refresh access token generation API",e)
        raise Exception("Error in refreshing access token"+str(e))
        

"""def writeTokenToFile(tokenDict):
    currentTimeInSecs=time.time()
    tokenOut={}
    tokenOut["accessToken"]=tokenDict["access_token"]
    tokenOut["accessTokenTimeStamp"]=currentTimeInSecs
    tokenOut["refreshToken"]=tokenDict["refresh_token"]
    tokenOut["expiresIn"]=tokenDict["expires_in"]
    with open(packageHD+"tokenSpecs.json","w") as f:
        json.dump(tokenOut,f)
"""        
def writeTokenToFile(tokenDict):
    currentTimeInSecs=time.time()
    tokenOut={}
    tokenOut["accessToken"]=tokenDict["access_token"]
    tokenOut["accessTokenTimeStamp"]=currentTimeInSecs
    tokenOut["refreshToken"]=tokenDict["refresh_token"]
    tokenOut["expiresIn"]=tokenDict["expires_in"]
    tokenStr=json.dumps(tokenOut)
    encrTokenBytes=aesEncryptStr(tokenStr)
    with open(packageHD+"tokenSpecsEncr.json","wb") as f:
        f.write(encrTokenBytes,f)

"""def loadTokenFromFile():
    try:
        with open(packageHD+"tokenSpecs.json","r") as f:
            tokenDict=json.load(f)
            return tokenDict
    except Exception as e:
        print("Error in loading token from file",e)"""
def loadTokenFromFile():
    cipherBytes=None
    with open(packageHD+"tokenSpecsEncr.json","rb") as f:
        cipherBytes=f.read()
    plainText=aesDecryptStr(cipherBytes=cipherBytes)
    tokenDict=json.loads(plainText.decode("utf-8"))
    return tokenDict

def isTokenValid(tokenDict):
    tokenExpiryPeriod=float(tokenDict["expiresIn"])
    tokenGeneratedPeriod=float(tokenDict["accessTokenTimeStamp"])
    currentTimeInSecs=time.time()
    if((tokenExpiryPeriod+tokenGeneratedPeriod)>(currentTimeInSecs+600)):
        return True
    else:
        return False

def generateAccessTokenFromCode_writeToFile(zohoAccountsServerUri,clientId,clientSecret,code):
    tokenResponse=generateAccessTokenFromCode(zohoAccountsServerUri,clientId,clientSecret,code)
    if (tokenResponse is not None):
        #write token details out to tokenSpecs.json file
        writeTokenToFile(tokenResponse)
        return tokenResponse
    else:
        return None

#can raise exception when access token couldn't be generated / loaded into memory
def getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code):
    
    print("Generating access token")
    loadedToken=loadTokenFromFile()
    tokenKeys=loadedToken.keys()
    if("generateFromCode" in tokenKeys):
        receivedToken=generateAccessTokenFromCode_writeToFile(zohoAccountsServerUri,clientId,clientSecret,code)
        if(receivedToken is not None):
            newToken={}
            newToken["accessToken"]=receivedToken["access_token"]
            newToken["refresh_Token"]=receivedToken["refresh_token"]
            newToken["expires_in"]=receivedToken["expires_in"]
            return newToken
        else:
            return None
    refreshToken=loadedToken["refreshToken"]
    if(not(isTokenValid(loadedToken))):
        print("Token expired, refreshing token")
        refreshedToken=RefreshAccessToken(zohoAccountsServerUri,refreshToken,clientId,clientSecret,None)
        refreshedAccessToken=refreshedToken["access_token"]
        loadedToken["accessToken"]=refreshedAccessToken
        loadedToken["access_token"]=refreshedAccessToken
        loadedToken["refresh_token"]=loadedToken["refreshToken"]
        loadedToken["expires_in"]=loadedToken["expiresIn"]
        if(refreshedAccessToken is not None):
            writeTokenToFile(loadedToken)
            #continue from here: return token
            return loadedToken
        else:
            return None
    else:
        return loadedToken

#checks accesstoken before calling an API
def checkAccessToken(zohoAccountsServerUri,clientId,clientSecret,code):
    accessToken=getAccessToken(zohoAccountsServerUri,clientId,clientSecret,code)
    oauthToken=accessToken["accessToken"]
    return oauthToken
"""
if __name__ == '__main__':
    main()"""