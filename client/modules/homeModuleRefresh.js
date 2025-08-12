fetch(apiUrl).then((data)=>{
    return data.json();
}).then((apiResp)=>{
    console.log("API resp is",apiResp);
    let usrsArr=apiResp.data;
    let carouselCardTemplate=document.getElementById("carouselCardClone");
    let carouselCardContainer=document.getElementById("catalogueCarouselParent")
    carouselCardContainer.innerHTML='';
    for(let usr of usrsArr)
    {
        let card=carouselCardTemplate.cloneNode(true);
        card.setAttribute("userId",usr.userId);
        card.setAttribute("callerName",usr.userName);
        let textElem=card.querySelector("#textElem");
        textElem.innerHTML=usr.userName;
        carouselCardContainer.appendChild(card);
    }
}).catch((err)=>{
    console.error("Error in get users API",err);
})

/*
carouselParent=document.getElementById("catalogueCarouselParent");
if(carouselSwipeInterval)
{
    clearInterval(carouselSwipeInterval);
    carouselSwipeInterval=null;
}
if(carouselParent)
{
    carouselChildren=carouselParent.children;
    carouselLen=carouselChildren.length;
    currentCardInd=0;
    carouselSwipeInterval=setInterval(()=>{
        if(currentCardInd+1>=carouselLen)
        {
            currentCardInd=0;
            carouselChildren[0].scrollIntoViewIfNeeded();
        }
        else
        {
            currentCardInd++;
            carouselChildren[currentCardInd].scrollIntoViewIfNeeded();
        }
    },2000);
}
*/