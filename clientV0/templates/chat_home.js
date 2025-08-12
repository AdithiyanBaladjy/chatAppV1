var contacts=[{contactName:"Maximoff Romanoff Anderson",contactId:"1",notificationsNumber:10},{contactName:"Johnson Mitchell Anderson",contactId:"2"},{contactName:"Mitchell Mccarthy Smith",contactId:"3"}];                    
var conversations=[{contactId:"1",conversations:[
    {from:"4",to:"1",msg:"Hi, How have you been?"},
    {from:"1",to:"4",msg:"Doing good, how are you?"},
    {from:"4",to:"1",msg:"So far, so good. How is the new project going?"},
    {from:"1",to:"4",msg:"It is in design & development phase."}
]},
{contactId:"2",conversations:[
    {from:"4",to:"2",msg:"Hi, How have you been?"},
    {from:"2",to:"4",msg:"Doing good, how are you?"},
    {from:"4",to:"2",msg:"So far, so good. How is the new project going?"},
    {from:"2",to:"4",msg:"It is in design & development phase."}]
},
{contactId:"3",conversations:[
    {from:"4",to:"3",msg:"Hi, How have you been?"},
    {from:"3",to:"4",msg:"Doing good, how are you?"},
    {from:"4",to:"3",msg:"So far, so good. How is the new project going?"},
    {from:"3",to:"4",msg:"It is in design & development phase."}]
}
];
var UserId="4";
function switchTheme(toggle)
{
    let state=toggle.getAttribute("state");
    if(state=="on")
    {
        document.body.classList.add("light-theme-colors");
        document.body.classList.remove("dark-theme-colors");
        console.log("deactivate dark theme");
    }
    else
    {
        document.body.classList.add("dark-theme-colors");
        document.body.classList.remove("light-theme-colors");
        console.log("Activate dark theme");
    }
}

function populateContacts(contacts)
{
    console.log("inside populate contacts");
    let contactCardParentElem=document.getElementById("contactCardsParent");
    let contactsLength=contacts.length;
    let contactCardClone=document.getElementById("contactCardClone");
    for(let i=0;i<contactsLength;i++)
    {
        let contactName=contacts[i].contactName;
        let contactId=contacts[i].contactId;
        let contactNotifs=contacts[i].notificationsNumber;
        let clonedContact=contactCardClone.cloneNode(true);
        clonedContact.id="contactCard"+contactId;
        clonedContactName=clonedContact.querySelector("#contactName");
        clonedContactNotif=clonedContact.querySelector("#notificationBubble");
        clonedContactName.innerHTML=contactName;
        clonedContactName.id="contactName"+contactId;
        clonedContact.addEventListener("click",()=>{showContactChat(contactId,contactName);});
        clonedContactNotif.id="notificationBubble"+contactId;
        contactCardParentElem.appendChild(clonedContact);
        if(contactNotifs)
        {
            setContactNotif(contactId,contactNotifs);
        }
        clonedContact.classList.remove("hide");
    }
}
function clearContactNotif(contactId)
{
    let contactNotif=document.getElementById("notificationBubble"+contactId);
    if(contactNotif)
    {
        contactNotif.innerHTML="";
        contactNotif.classList.remove("contact-notif-bubble");
    }
}
function setContactNotif(contactId,notifNumber)
{
    console.log("inside Set contact");
    let contactNotif=document.getElementById("notificationBubble"+contactId);
    if(contactNotif)
    {
        contactNotif.classList.add("contact-notif-bubble");
        contactNotif.innerHTML=notifNumber;
    }
}
function showContactChat(contactId,contactName)
{
    let clickedElem=document.getElementById("contactCard"+contactId);
    let previouslySelectedElem=document.getElementsByClassName("contact-selected");
    let contactNameElem=document.getElementById("chatContactName");
    let contactStatusElem=document.getElementById("contactStatus");
    if(previouslySelectedElem.length)
    {
        previouslySelectedElem[0].classList.remove("contact-selected");
    }
    clickedElem.classList.add("contact-selected");
    clearContactNotif(contactId);
    contactNameElem.innerHTML=contactName;
    contactStatusElem.innerHTML="Offline";
    console.log("contact clicked",contactId);
}
function populateChat(chats)
{
    
}
function getConversations(conversationId)
{
    let chats;
    for(let c of conversations)
    {
        if(c["contactId"]==conversationId)
        {
            chats=c["conversations"];
        }
    }
    if(chats)
    {

    }
    else
    {

    }
}
window.onload=(event)=>{
    console.log("window loaded",event);
    populateContacts(contacts);
};