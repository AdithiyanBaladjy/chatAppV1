var currentCardInd=0;
var carouselLen=0;
var carouselSwipeInterval=null;
document.getElementById("greetingsDiv").innerHTML=`Hello ${loggedInUsrName}`;

let apiUrl=`${apiProtocol}://${serverDomain}:${portNumber}/api/getUsers/${loggedInUsrId}`;


function callUser(btnRef)
{
    let userCard=btnRef.parentNode;
    let usrId=userCard.getAttribute("userId");
    incomingCallerName=userCard.getAttribute("callerName");
    incomingCallerId=usrId;
    socket.send(`call:${usrId}`);
}
