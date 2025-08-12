//code for websocket

socket = null
callSocket = null
function establishCallConnection()
{
    callSocket = new WebSocket(`wss://${serverDomain}:${portNumber}/api/call/${loggedInUsrId}/${userAccessToken}/convId/${currentConvoId}`);
                callSocket.addEventListener('open', (event) => {
                    console.log('Connected to call socket.');
                });
                callSocket.addEventListener('close', (event) => {
                    console.log('call socket closed.');

                //
                //
                });
                callSocket.onmessage=(event)=>{
                    if(typeof event.data==='string')
                    {
                        if(typeof event.data==='string')
                        {
                            let dataPrefix=event.data.split(":")[0];
                            if(dataPrefix=="connectionClosed")
                            {
                                //re-initiate connection after authentication
                                refreshAccessToken().then((data)=>{
                                    if(data==true)
                                    {
                                        establishCallConnection();
                                    }
                                }).catch((err)=>{
                                    console.error("Error in access token refresh",err);
                                    setTimeout(()=>{
                                        establishCallConnection();
                                    },200);
                                });
                            }
                        }
                    }
                };
}
function establishSocketConnection()
{
    socket = new WebSocket(`wss://${serverDomain}:${portNumber}/api/ws/${loggedInUsrId}/${userAccessToken}`);

    //Add socket's event listeners
    // Event handler for when the connection is established
    socket.addEventListener('open', (event) => {
        console.log('Connected to server.');
    });

    // Event handler for receiving messages from the server
    socket.onmessage = (event) => {
        console.log("You received data from server",event.data);
        if(typeof event.data==='string')
        {
            let dataPrefix=event.data.split(":")[0];
            if(dataPrefix=='callFrom')
            {

                let dataSuffix=event.data.split(":")[1];
                incomingCallerId=dataSuffix;
                incomingCallerName=event.data.split(":")[2];
                loadModule("oneOrderComponent","homeModulePopUpContainer");
                console.log("You are receiving a call from user:",dataSuffix);
            }
            if(dataPrefix=='callConnected')
            {
                currentConvoId=event.data.split(":")[1];
                loadModule("oneOrderComponent","homeModulePopUpContainer");
                establishCallConnection();
                //
                //

                //Audio sampling code
                let audioIN = { audio: true };
                navigator.mediaDevices.getUserMedia(audioIN).then(function (mediaStreamObj)
                {
                    let mediaRecorder = new MediaRecorder(mediaStreamObj);
                    // Chunk array to store the audio data 
                    let dataArray = [];
                    mediaRecorder.ondataavailable = function (ev) {
                        dataArray.push(ev.data);
                    }
                    mediaRecorder.start();
                    audioSampleInterval=setInterval(()=>{
                        mediaRecorder.stop();
                        mediaRecorder.start();
                    },100);
                    //
                    mediaRecorder.onstop = function (ev) {
 
                        // blob of type mp3
                        let audioData = new Blob(dataArray, 
                              { 'type': 'audio/mp3' });
                     
                    // After fill up the chunk 
                    // array make it empty
                    dataArray = [];
                    callSocket.send(audioData);
                    }
                //
                })
            //
            }
            else if(dataPrefix=="connectionClosed")
            {
                closeMsg=event.data.split(":")[1];
                if(closeMsg=="token expired")
                {
                    //refresh access token and connect web-socket again
                    refreshAccessToken().then((data)=>{
                        if(data==true)
                        {
                            establishSocketConnection();
                        }
                    }).catch((err)=>{
                        console.error("Error in access token refresh",err);
                        setTimeout(()=>{
                            establishSocketConnection();
                        },200);
                    });
                }
            }
    }
    else if(event.data instanceof Blob)
    {
        // let audioData= new Blob(event.data,{"type":"audio/mp3"});
        let audioSrc=window.URL.createObjectURL(event.data);
        let audioElem=new Audio(audioSrc)
        audioElem.play();
    }
}

// Event handler for when the connection is closed
socket.addEventListener('close', (event) => {
    console.log('Connection closed.');
});
callSocket.addEventListener('close',(event)=>{
    closeModule('oneOrderComponent');
});
    //
}
function homeMenuClick(btnElem,menuName)
{
    let btns=btnElem.parentNode.children;
    for(let btn of btns)
    {
        btn.classList.remove("selected-icon-container");
    }
    btnElem.classList.add("selected-icon-container");

    loadModule(menuName,"homeScreenMenuParent");
}

establishSocketConnection();