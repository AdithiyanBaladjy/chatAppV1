import tink
from tink import daead
from tink import secret_key_access
import json

daead.register()
keyset = r"""{
      "key": [{
          "keyData": {
              "keyMaterialType":
                  "SYMMETRIC",
              "typeUrl":
                  "type.googleapis.com/google.crypto.tink.AesSivKey",
              "value":
                  "EkAl9HCMmKTN2p5V186uhZpJQ+tivyc4IKyE+opg6SsEbWQ/WesWHzwCRrlgRuxdaggvgMzwWhjPnkk9gptBnGLK"
          },
          "keyId": 1919301694,
          "outputPrefixType": "TINK",
          "status": "ENABLED"
      }],
      "primaryKeyId": 1919301694
  }"""

#Input string - inputStr
#Output Bytes - cipherTxt
def aesEncryptStr(inputStr):
    keyset_handle = tink.json_proto_keyset_format.parse(keyset, secret_key_access.TOKEN)
    primitive = keyset_handle.primitive(daead.DeterministicAead)
    ciphertext = primitive.encrypt_deterministically(inputStr.encode("utf-8"),b'context')
    return ciphertext

#Input Bytes - cipherBytes
#Output String - plain text
def aesDecryptStr(cipherBytes):
    keyset_handle = tink.json_proto_keyset_format.parse(keyset, secret_key_access.TOKEN)
    primitive = keyset_handle.primitive(daead.DeterministicAead)
    output = primitive.decrypt_deterministically(cipherBytes,b'context')
    return output.decode("utf-8")

if __name__=="__main__":
    # inputStr="""{"accessToken": "1000.07956db5a79746315416089826ce2b1f.d798039f16ca71ed9bc77ae88e824a1a", "accessTokenTimeStamp": 1741602061.317291, "refreshToken": "1000.99a8007780e7a789cf4b0a61ae840de4.d1087742a5e6d6c2486978051a46e6f9", "expiresIn": 3600}"""
    # print(inputStr)
    # cipherBytes=aesEncryptStr(inputStr)
    # with open("cipherTxt.txt","wb") as f:
    #     f.write(cipherBytes)
    """tokenDict=None
    with open("oauthUtils/tokenSpecs.json","r") as f:
        tokenDict=json.load(f)
    tokenStr=json.dumps(tokenDict)
    cipherBytes=aesEncryptStr(tokenStr)
    with open("oauthUtils//tokenSpecsEncr.txt","wb+") as f:
        f.write(cipherBytes)
    """
    cipherBytes=None
    with open("oauthUtils/tokenSpecsEncr.txt","rb") as f:
        cipherBytes=f.read()        
        pass
    plainTxt=aesDecryptStr(cipherBytes)
    print(plainTxt) 