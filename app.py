from flask import Flask, redirect, url_for, render_template, request as flaskReq, send_from_directory, jsonify
from flask_sock import Sock
import traceback

#imports required for authentication
import sqlite3
import secrets
import hashlib
from datetime import datetime, timedelta
import os
#


loggedInUsers=[]
"""
[
    {
        userName:xyz,
        userId:123
    },
    {
        userName:xyz,
        userId:123
    },
]
"""
loggedInSessions={}
convos={}
#Structure
"""
{
    <convId>:{
        "callers":[List of usrIds],
        "sessions":[{"callerId":<usId>,"session":<wsSessionObj}]
    },..
}
"""

startUserId=0
startConvoId=0

# Authentication Configuration
DATABASE = 'auth.db'
ACCESS_TOKEN_EXPIRY_MINUTES = 10  # Can be changed as needed
recordsLimit = 20

#functions needed in authentication

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Refresh tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Access tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def generate_token():
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()
#



app=Flask(__name__)
sock=Sock(app)

def getUserNameById(usersListObj,usrId):
    for user in usersListObj:
        print(user)
        if str(user.get("userId")) == str(usrId):
            return user.get("userName")

@app.route('/<file_name>')
def render_static(file_name):
    print("serving static file",file_name)
    return send_from_directory('client', file_name)


@app.route('/<directory>/<file_name>')
def render_directory(directory,file_name):
    print("Rendering from directory",directory,file_name)
    return send_from_directory('client',directory+"/"+file_name)

@app.route('/<path:path>') #Everything else just goes by filename
def sendPath(path):
	print(path)
	return send_from_directory('client', path)

@app.route('/')
def render_index():
    return redirect('/index.html')

@app.route('/api/login/<userName>')
def signIn(userName):
    global startUserId
    startUserId+=1
    userObj={}
    userObj['userName']=userName
    userObj['userId']=str(startUserId)
    loggedInUsers.append(userObj)
    retObj={}
    retObj['status']='Success'
    retObj['data']=userObj
    return retObj

@app.route('/api/getUsers/<userId>')
def getUsers(userId):
    """
    input: header: {authToken:xyz},
    output: {status:Success,data:[{userId:123,userName:abc},{userId:123,userName:abc}]}
    """
    try:
        authToken=flaskReq.headers.get("authToken")
        if not (userId or authToken):
            return jsonify({"Status":"Failure","error":"userId and authToken are required"})
        authStatus=authenticateToken(userId,authToken)
        if(authStatus["status"]!="success"):
            return jsonify({"status":"failure","error":authStatus["reason"]})
        retObj={}
        retObj["status"]='Success'
        retObj["data"]=loggedInUsers
        return retObj
    except Exception as e:
        print("Error in GET /api/getUsers/<userId>",e)
        traceback.print_exc()
        return jsonify({"Status":"Failure","error":str(e)})

@app.route('/api/searchUsers',methods=['POST'])
def searchUsers():
    """
    Returns the users data whose userName match with the input query.
    input: header: {authToken:xyz}, post body:{userId:123,query:abc}
    output: {status:Success,data:[{userId:123,userName:abc},{userId:123,userName:abc}]}
    """
    try:
        data = flaskReq.get_json()
        userId=data.get("userId")
        queryStr=data.get("query")
        authToken=flaskReq.headers.get("authToken")
        if not (userId or authToken or queryStr):
            return jsonify({"Status":"Failure","error":"userId, authToken and query are required"})
        authStatus=authenticateToken(userId,authToken)
        if(authStatus["status"]!="success"):
            return jsonify({"status":"failure","error":authStatus["reason"]})
        retObj={}
        retObj["status"]='Success'
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id, username FROM users WHERE username like %?% LIMIT ?', (queryStr,recordsLimit))
        results=cursor.fetchall()
        if not results:
            results=[]
        retObj["data"]=results
        return retObj
    except Exception as e:
        print("Error in POST /api/searchUsers",e)
        traceback.print_exc()
        return jsonify({"Status":"Failure","error":str(e)})
    

@sock.route('/api/ws/<userId>/<authToken>')
def sessionConnect(ws,userId,authToken):
    global loggedInSessions, convos, startConvoId
    print("\n")
    print("websocket running",userId)
    authStatus=authenticateToken(userId,authToken)
    if not(userId and authToken):
        ws.send("connectionClosed:{0}".format("userId and authToken required"))
        ws.close()
    if(authStatus["status"]!="success"):
        reason=authStatus["reason"]
        ws.send("connectionClosed:{0}".format(reason))
        ws.close()
        if (loggedInSessions.get(str(userId))):
            del loggedInSessions[str(userId)]
        return
    userSession=loggedInSessions.get(str(userId))
    if(userSession is None):    
        loggedInSessions[str(userId)]=ws
    try:
        while True:
            data=ws.receive()
            if((type(data)==str)and(data.split(":")[0]=="call")):
                receiverId=data.split(":")[1]
                
                print("Call receiverId: ",receiverId)
                print("Logged in user sessions",loggedInSessions)
                print("Logged in users",loggedInUsers)
                receiverSession=loggedInSessions.get(str(receiverId))
                # callerName=loggedInUsers.get(userId)
                callerName=getUserNameById(loggedInUsers,userId)
                receiverSession.send("callFrom:"+str(userId)+":"+str(callerName))
            if((type(data)==str)and(data.split(":")[0]=="connectCall")):
                #create a conversation object that has two attributes
                #callers:[callerIds]
                #callerSessions[{userId:<userId>,sessionObj:<wsObj>},{userId:<userId>,sessionObj:<wsObj>}]
                callerIds=[data.split(":")[1],data.split(":")[2]]
                convos[str(startConvoId)]={
                    "callers":callerIds
                }
                convoSessions=[]
                for callerId in callerIds:
                    sessionObj={}
                    sessionObj["usrId"]=callerId
                    sessionObj["session"]=loggedInSessions.get(str(callerId))
                    convoSessions.append(sessionObj)
                convos[str(startConvoId)]["sessions"]=convoSessions
                for sess in convoSessions:
                    wsSess=sess["session"]
                    wsSess.send("callConnected:"+str(startConvoId))
                startConvoId+=1
            print(data=="Hi")
            ws.send(data)
    except Exception as e:
        # loggedInSessions[userId]=None
        print("Exception in ws",e)
        traceback.print_exc()
        

@sock.route('/api/call/<userId>/<authToken>/convId/<convId>')
def callConnect(ws,userId,authToken,convId):
    global loggedInSessions
    print(convos)
    print("call in:",convId)
    if not(userId and authToken):
        ws.send("connectionClosed:{0}".format("userId and authToken required"))
        ws.close()
    authStatus=authenticateToken(userId,authToken)
    if(authStatus["status"]!="success"):
        reason=authStatus["reason"]
        ws.send("connectionClosed:{0}".format(reason))
        ws.close()
    convoObj=convos.get(convId)
    convoSessions=convoObj.get("sessions")
    try:
        while True:
            data=ws.receive()
            if((type(data)==str)and(data.split(":")[0]=="disconnectCall")):
                for sess in convoSessions:
                    sessObj=sess["session"]
                    sessObj.close()
                    del convos[convId]
                return
            print("Blob received")
            print(data)
            for sess in convoSessions:
                if(str(sess["usrId"])!=str(userId)):
                    sessObj=sess["session"]
                    sessObj.send(data)
    except Exception as e:
        # loggedInSessions[userId]=None
        print("Exception in call ws session",e)
        traceback.print_exc()

#functions exposed for authentication

@app.route('/signup', methods=['POST'])
def signup():
    """
    Sign up a new user
    Input: {"username": "string", "password_hash": "string"}
    Output: {"refresh_token": "string", "user_id": int}
    """
    try:
        data = flaskReq.get_json()
        username = data.get('username')
        password_hash = data.get('password_hash')
        
        if not username or not password_hash:
            return jsonify({'error': 'username and password_hash are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            return jsonify({'error': 'User already exists'}), 409
        
        # Create new user
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        user_id = cursor.lastrowid
        
        # Generate refresh token
        refresh_token = generate_token()
        cursor.execute(
            'INSERT INTO refresh_tokens (user_id, token) VALUES (?, ?)',
            (user_id, refresh_token)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'refresh_token': refresh_token,
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/authenticate', methods=['POST'])
def authenticate():
    """
    Authenticate user credentials
    Input: {"username": "string", "password_hash": "string"}
    Output: {"refresh_token": "string", "user_id": int}
    """
    try:
        data = flaskReq.get_json()
        username = data.get('username')
        password_hash = data.get('password_hash')
        
        if not username or not password_hash:
            return jsonify({'error': 'Username and password_hash are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Authenticate user
        cursor.execute(
            'SELECT id FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        user_id = user[0]
        userObj={}
        userObj['userName']=username
        userObj['userId']=str(user_id)
        loggedInUsers.append(userObj)
        # Get existing refresh token or create new one
        cursor.execute(
            'SELECT token FROM refresh_tokens WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
            (user_id,)
        )
        existing_token = cursor.fetchone()
        
        if existing_token:
            refresh_token = existing_token[0]
        else:
            refresh_token = generate_token()
            cursor.execute(
                'INSERT INTO refresh_tokens (user_id, token) VALUES (?, ?)',
                (user_id, refresh_token)
            )
            conn.commit()
        
        conn.close()
        
        return jsonify({
            'refresh_token': refresh_token,
            'user_id': user_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-access-token', methods=['POST'])
def generate_access_token():
    """
    Generate access token using refresh token
    Input: {"user_id": int, "refresh_token": "string"}
    Output: {"access_token": "string", "expires_at": "string"}
    """
    try:
        data = flaskReq.get_json()
        user_id = data.get('user_id')
        refresh_token = data.get('refresh_token')
        
        if not user_id or not refresh_token:
            return jsonify({'error': 'user_id and refresh_token are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Validate refresh token
        cursor.execute(
            'SELECT id FROM refresh_tokens WHERE user_id = ? AND token = ?',
            (user_id, refresh_token)
        )
        if not cursor.fetchone():
            return jsonify({'error': 'Invalid refresh token'}), 401
        
        # Generate access token
        access_token = generate_token()
        expires_at = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)
        
        # Clean up expired access tokens for this user
        cursor.execute(
            'DELETE FROM access_tokens WHERE user_id = ? AND expires_at < ?',
            (user_id, datetime.now())
        )
        
        # Store new access token
        cursor.execute(
            'INSERT INTO access_tokens (user_id, token, expires_at) VALUES (?, ?, ?)',
            (user_id, access_token, expires_at)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'access_token': access_token,
            'expires_at': expires_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sign-out-user',methods=['POST'])
def sign_out_user():
    """
    input: header: {authToken:xyz}, payload: {userId:123}
    output: {status:success | failure, error:"error msg"}
    """
    try:
        data=flaskReq.get_json()
        userId=data.get("userId")
        print("fetched userId")
        accessToken=flaskReq.headers.get("authToken")
        print("fetched access token")
        if not(userId and accessToken):
            return jsonify({"status":"failure","error":"userId and accessToken are required"}), 400
        authStatus=authenticateToken(userId,accessToken)
        if(authStatus["status"]!="success"):
            return jsonify({"status":"failure","error":authStatus["reason"]})
        else:
            for i in range(len(loggedInUsers)):
                user=loggedInUsers[i]
                if(user["userId"]==str(userId)):
                    loggedInUsers.pop(i)
                    print(loggedInSessions)
                    loggedInSessions[str(userId)].close()
                    del loggedInSessions[str(userId)]
            return jsonify({"status":"success","data":"user signed out"}), 200
        
    except Exception as e:
        print(e)
        traceback.print_exc()
        return jsonify({"status":"failure","error":str(e)}), 500


@app.route('/authenticate-token', methods=['POST'])
def authenticate_token():
    """
    Authenticate access token
    Input: {"user_id": int, "access_token": "string"}
    Output: {"valid": bool, "expires_at": "string"}
    """
    try:
        data = flaskReq.get_json()
        user_id = data.get('user_id')
        access_token = data.get('access_token')
        
        if not user_id or not access_token:
            return jsonify({'error': 'user_id and access_token are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if access token exists and is not expired
        cursor.execute(
            'SELECT expires_at FROM access_tokens WHERE user_id = ? AND token = ? AND expires_at > ?',
            (user_id, access_token, datetime.now())
        )
        token_data = cursor.fetchone()
        
        conn.close()
        
        if token_data:
            return jsonify({
                'valid': True,
                'expires_at': token_data[0]
            }), 200
        else:
            return jsonify({
                'valid': False,
                'message': 'Token is invalid or expired'
            }), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

#
def authenticateToken(userId,accessToken):
    """
    authenticates access token
    Inputs: userId, accessToken
    Output:{status:"success" | "failure",reason: "invalid token" | "token expired"}
    """
    conn = get_db()
    cursor = conn.cursor()
    retObj=None
        
    # Check if access token exists and is not expired
    cursor.execute(
            'SELECT expires_at FROM access_tokens WHERE user_id = ? AND token = ? AND expires_at > ?',
            (userId, accessToken, datetime.now())
    )
    token_data = cursor.fetchone()
    if(token_data):
        retObj={"status":"success"}
    else:
        cursor.execute(
            'SELECT expires_at FROM access_tokens WHERE user_id= ? AND token= ?',
            (userId,accessToken)
        )
        token_data=cursor.fetchone()
        if(token_data):
            retObj={"status":"failure","reason":"token expired"}
        else:
            retObj={"status":"failure","reason":"invalid token"}
    conn.close()
    return retObj

if __name__=='__main__':
    init_db()
    app.run('0.0.0.0',8000,ssl_context=('cert.pem', 'key.pem'))