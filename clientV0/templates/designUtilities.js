function main(){
    //configure toggle switches
    let toggleElems=document.getElementsByClassName("toggle-container");
    for(i=0;i<toggleElems.length;i++)
    {
        toggleElems[i].innerHTML=`<div class="toggle-switch toggle-switch-left"></div>`;
        toggleElems[i].setAttribute("state","off");
        toggleElems[i].addEventListener("click",(evt)=>{toggleSwitch(evt);});
    }
}
function toggleSwitch(evt)
{
    let target=evt.currentTarget;
    let toggleSwitch=target.children[0];
    console.log("state is",target.getAttribute("state"));
    if(target.getAttribute("state")=="off")
    {
        //switch on the toggle
        toggleSwitch.classList.remove("toggle-switch-left");
        toggleSwitch.classList.add("toggle-switch-right");
        target.setAttribute("state","on");
        target.classList.add("toggle-container-active");
    }
    else
    {
        //switch off the toggle
        toggleSwitch.classList.remove("toggle-switch-right");
        toggleSwitch.classList.add("toggle-switch-left");
        target.setAttribute("state","off");
        target.classList.remove("toggle-container-active");
    }
}
main();