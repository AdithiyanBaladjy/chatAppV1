function cutCall()
{
    if(!callSocket)
    {
        callSocket.send("disconnectCall:");
    }
}

function closeComponent()
{
    // productDropDown.destroyDependencies();
    cutCall();
    closeModule('oneOrderComponent');
}

function connectCall()
{
    socket.send(`connectCall:${loggedInUsrId}:${incomingCallerId}`);
}