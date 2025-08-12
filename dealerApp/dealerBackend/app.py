import subprocess
import requests
import json

# Using system() method to
# execute shell commands
try:
    from flask import Flask
except Exception:
    subprocess.Popen('pip3 install flask', shell=True)
    from flask import Flask
import os

isUatInstance=False
hostName=None
app = Flask(__name__)

crmCreateApiUrl="""https://www.zohoapis.in/crm/v7/functions/createtestorder/actions/execute?auth_type=apikey&zapikey=1003.24453feab3f3c4564420bfb3998c0d5c.5a46123ca473488f4ad7b174a3270dd0"""

@app.route('/createOrder/<orderName>')
def index(orderName):
    reqDict={
        "orderName":orderName
    }
    header={
        "Content-Type":"application/json"
    }
    print(reqDict)
    resp=requests.post(crmCreateApiUrl,data=json.dumps(reqDict),headers=header)
    apiOut=None
    if resp.status_code == 200 or resp.status_code == 201:
        print("Request successful!")
        print("Response content:", resp.text) # Print the raw response content
        try:
            response_json = resp.json() # Try to parse response as JSON
            print("Response JSON:", response_json)
            apiOut=response_json
        except json.JSONDecodeError:
            print("Response is not JSON")
    else:
        print(f"Request failed with status code: {resp.status_code}")
        print("Response content:", resp.text)
        apiOut=resp.text
    return apiOut
    
listen_port = os.getenv('X_ZOHO_CATALYST_LISTEN_PORT', 9000)
if isUatInstance==True:
    hostName='127.0.0.1'
else:
    hostName='0.0.0.0'

app.run(host=hostName, port = listen_port)