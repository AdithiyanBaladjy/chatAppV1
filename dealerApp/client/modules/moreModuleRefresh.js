modeIconContainer=document.getElementById("modeIconContainer");
modeIconText=document.getElementById("modeIconText");
if(modeIconContainer&&modeIconText)
{
    if(lightMode)
    {
        modeIconContainer.innerHTML="<i class='fa fa-moon'></i>";
        modeIconText.innerHTML="Switch Dark";
    }
    else
    {
        modeIconContainer.innerHTML="<i class='fa fa-sun'></i>";
        modeIconText.innerHTML="Switch Light";

    }
}
console.log("Inside more module refresh");