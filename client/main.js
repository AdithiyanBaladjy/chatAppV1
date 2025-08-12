var serverDomain="172.20.10.3";
serverDomain="10.15.209.241";
var portNumber="8000";
var apiProtocol='https';
var lightMode=true;
var modules={
    "page1":{
        "index":"page1.html",
        "script":["page1.js"],
        "refreshScript":["page1Refresh.js"]
    },
    "signin":{
        "index":"signin.html",
        "script":["signin.js"]
    },
    "homeScreen":{
        "index":"homeScreen.html",
        "script":["homeScreen.js"],
        "refreshScript":["homeScreenRefresh.js"]
    },
    "homeModule":{
        "index":"homeModule.html",
        "script":["homeModule.js"],
        "refreshScript":["homeModuleRefresh.js"]
    },
    "orderModule":{
        "index":"orderModule.html",
        "script":["orderModule.js"],
        "refreshScript":["orderModuleRefresh.js"]
    },
    "scanModule":{
        "index":"scanModule.html",
        "script":["scanModule.js"],
        "refreshScript":["scanModuleRefresh.js"]
    },
    "moreModule":{
        "index":"moreModule.html",
        "script":["moreModule.js"],
        "refreshScript":["moreModuleRefresh.js"]
    },
    "oneOrderComponent":{
        "index":"oneOrderComponent.html",
        "script":["oneOrderComponent.js"],
        "refreshScript":["oneOrderComponentRefresh.js"]
    }
};
/*
serverDomain= (window.location.href.split(":")[1]).split(":")[0];
*/
var isSignedIn=false;
var userRefreshToken;
var userAccessToken;

function loadTemplate(href)
{
    if(href)
    {
        var xmlhttp = new XMLHttpRequest();
        let moduleLocation="./modules/";
        xmlhttp.open("GET", moduleLocation+href, false);
        xmlhttp.send();
        return xmlhttp.responseText;
    }
    else
    {
        return "Module not registered";
    }
  
}
function loadScriptFile(url)
{
   let moduleLocation="./modules/";
   let scriptElem=document.querySelector(`[moduleName='${moduleLocation+url}']`);
   if(!scriptElem)
   {
        scriptElem=document.createElement("script");
        scriptElem.src=moduleLocation+url;
        scriptElem.setAttribute("moduleName",moduleLocation+url);
        document.head.appendChild(scriptElem);
   }
   
}
function removeScriptFile(url)
{
    let moduleLocation='./modules/';
    let scriptElem=document.querySelector(`[moduleName='${moduleLocation+url}']`);
    if(scriptElem)
    {
        scriptElem.remove();
    }
}
function loadModule(moduleName,parentContainer)
{
    let moduleDependencies=modules[moduleName];
    if(moduleDependencies)
    {
        let indexFile=moduleDependencies["index"];
        let scriptArr=moduleDependencies["script"];
        let refreshScripts=moduleDependencies["refreshScript"];
        let parentElem=document.getElementById(parentContainer);
        parentElem.innerHTML='';
        parentElem.innerHTML=loadTemplate(indexFile);
        parentElem.children[0].id=moduleName;
        for(let script of scriptArr)
        {
            loadScriptFile(script);
        }
        if(refreshScripts&&refreshScripts.length>0)
        {
            for(let script of refreshScripts)
            {
                removeScriptFile(script);
                loadScriptFile(script);
            }
        }
    }
}
//removes the given module from DOM
function closeModule(moduleName)
{
    let module=document.getElementById(moduleName);
    if(module)
    {
        module.parentNode.innerHTML='';
        let removedModule=modules[moduleName];
        if(removedModule)
        {
            let associatedScripts=removedModule["script"];
            for(let script of associatedScripts)
            {
                removeScriptFile(script);
            }
        }
    }
    
}
function loadApp(){
    if(!isSignedIn)
    {
        loadModule("signin","topParent");
    }
    document.body.classList.add("light-theme");
    // document.body.classList.add("dark-theme");
}
function signOut(){
    isSignedIn=false;
    userRefreshToken=null;
    //
    let signOutUrl=`${apiProtocol}://${serverDomain}:${portNumber}/sign-out-user`;
    console.log("User access token",userAccessToken);
    fetch(signOutUrl,{
        headers:{
            'Accept':"application/json",
            'Content-type':"application/json",
            'authToken':`${userAccessToken}`
        },
        method:'POST',
        body:JSON.stringify({
            userId:loggedInUsrId
        })
    }).then((data)=>{
        return data.json();
    }).then((apiResp)=>{
        if(apiResp.status=="success")
        {
            loadModule("signin","topParent");
        }
        else
        {
            refreshTokenIfNeeded(apiResp);
        }
    }).catch((err)=>{
        refreshTokenIfNeeded(err);
        console.error("Error in sign-out API",err);
    });
    //
    //route to logged-in view
    // loadModule("signin","topParent");
}
loadApp();

//Code required for the app
var loggedInUsrId;
var loggedInUsrName;
//code for websocket
var socket;
var incomingCallerName;
var incomingCallerId;
var currentConvoId;
var callSocket;
var audioSampleInterval;

/*
setInterval(()=>{
    socket.send("Hi");
},100);
*/

function checkLogin()
{
    if(!userRefreshToken)
    {
        loadModule("signin","topParent");
    }
}

function refreshAccessToken()
{

    let tokenGenUrl=`${apiProtocol}://${serverDomain}:${portNumber}/generate-access-token`;
                /* Access-token generation */
    return fetch(tokenGenUrl,{
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
               
                      },
                    method:'POST',
                    body:JSON.stringify({
                        user_id:`${loggedInUsrId}`,
                        refresh_token:userRefreshToken
                    })
                }).then((data)=>{
                    return data.json();
                }).then((resp)=>{
                    console.log("Access token generated",resp);
                    if(resp.access_token)
                    {
                        userAccessToken=resp.access_token;
                    }
                    return true;
                }).catch((err)=>{
                    console.error("Error in access token generation",err);
                    return false;
                })
}

//return true -> the caller should redo-the activity
// false -> caller need not redo the activity, can continue parsing the response
function refreshTokenIfNeeded(apiResp)
{
    if(apiResp.error && apiResp.error=="token expired")
    {
        refreshAccessToken().then((data)=>{
            if(data==true)
            {
                console.log("Access token refreshed");
            }
        }).catch((err)=>{
            console.error("Error in access token refresh",err);
            
        });
    }
}