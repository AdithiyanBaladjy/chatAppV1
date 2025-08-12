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
var isSignedIn=false;
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
    //route to logged-in view
    loadModule("signin","topParent");
}
loadApp();