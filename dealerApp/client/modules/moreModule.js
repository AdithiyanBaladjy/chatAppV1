function switchMode()
{
    if(lightMode)
    {
        lightMode=false;
        document.body.classList.add("dark-theme");
        document.body.classList.remove("light-theme");
    }
    else
    {
        lightMode=true;
        document.body.classList.remove("dark-theme");
        document.body.classList.add("light-theme");
    }
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
}