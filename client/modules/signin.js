let infoElem=document.getElementById("infoTag");

/*
function signInUser()
{
    let userName=document.getElementById("signInUserName").value;
    if(userName)
    {
        let userNameEncoded=encodeURI(userName);
        let signInUrl=`${apiProtocol}://${serverDomain}:${portNumber}/api/login/${userNameEncoded}`;
        fetch(signInUrl).then((data)=>{
            return data.json();
        }).then((resp)=>{
            loggedInUsrId=resp.data.userId;
            loggedInUsrName=resp.data.userName;
            console.log("Response from Sign in API",resp);

            isSignedIn=true;
            //route to logged-in view
            loadModule("homeScreen","topParent");
        }).catch((err)=>{
            console.error("Error from Sign-in API",err);
        })
    }
    
}
*/

function signInUser()
{
    let userName=document.getElementById("signInUserName").value;
    let pwd=document.getElementById("signInPassword").value;
    if(userName && pwd)
    {
        // let userNameEncoded=encodeURI(userName);
        let signInUrl=`${apiProtocol}://${serverDomain}:${portNumber}/authenticate`;
        fetch(signInUrl,{
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
       
              },
            method:'POST',
            body:JSON.stringify({
                username:userName,
                password_hash:pwd
            })
        }).then((data)=>{
            return data.json();
        }).then((resp)=>{
            
            console.log("Response from Sign up API",resp);
            if(resp.refresh_token)
            {
                //sign-up successful
                userRefreshToken=resp.refresh_token;
                loggedInUsrId=resp.user_id;
                loggedInUsrName=userName;
                infoElem.innerHTML=`Signing into the application..`;
                //generate access token and sign-in user
                let tokenGenUrl=`${apiProtocol}://${serverDomain}:${portNumber}/generate-access-token`;
                /* Access-token generation */
                fetch(tokenGenUrl,{
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
               
                      },
                    method:'POST',
                    body:JSON.stringify({
                        user_id:loggedInUsrId,
                        refresh_token:userRefreshToken
                    })
                }).then((data)=>{
                    return data.json();
                }).then((resp)=>{
                    console.log("Access token generated",resp);
                    if(resp.access_token)
                    {
                        userAccessToken=resp.access_token;
                        loadModule("homeScreen","topParent");
                    }
                    
                }).catch((err)=>{
                    console.error("Error in access token generation",err);
                    infoElem.innerHTML=`Sign In failed. Reason:${err}`;
                })
            }
            else
            {
                let errMsg=resp.error;
                infoElem.innerHTML=`Sign up failed. Reason:${errMsg}`;
            }

        }).catch((err)=>{
            console.error("Error from Sign-up API",err);
            infoElem.innerHTML=`Sign In failed. Reason:${err}`;
        })
    }
    
}

function signUpUser()
{
    let userName=document.getElementById("signInUserName").value;
    let pwd=document.getElementById("signInPassword").value;
    if(userName && pwd)
    {
        // let userNameEncoded=encodeURI(userName);
        let signUpUrl=`${apiProtocol}://${serverDomain}:${portNumber}/signup`;
        fetch(signUpUrl,{
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
       
              },
            method:'POST',
            body:JSON.stringify({
                username:userName,
                password_hash:pwd
            })
        }).then((data)=>{
            return data.json();
        }).then((resp)=>{
            
            console.log("Response from Sign up API",resp);
            if(resp.refresh_token)
            {
                //sign-up successful
                userRefreshToken=resp.refresh_token;
                loggedInUsrId=resp.user_id;
                loggedInUsrName=userName;
                infoElem.innerHTML=`Sign-up successful. Signing into the application..`;
                //generate access token and sign-in user
                let tokenGenUrl=`${apiProtocol}://${serverDomain}:${portNumber}/generate-access-token`;
                /* Access-token generation */
                fetch(tokenGenUrl,{
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
               
                      },
                    method:'POST',
                    body:JSON.stringify({
                        user_id:loggedInUsrId,
                        refresh_token:userRefreshToken
                    })
                }).then((data)=>{
                    return data.json();
                }).then((resp)=>{
                    console.log("Access token generated",resp);
                    if(resp.access_token)
                    {
                        userAccessToken=resp.access_token;
                        loadModule("homeScreen","topParent");
                    }
                }).catch((err)=>{
                    console.error("Error in access token generation",err);
                })
            }
            else
            {
                let errMsg=resp.error;
                infoElem.innerHTML=`Sign up failed. Reason:${errMsg}`;
            }

        }).catch((err)=>{
            console.error("Error from Sign-up API",err);
            infoElem.innerHTML=`Sign up failed. Reason:${err}`;
        })
    }
    
}