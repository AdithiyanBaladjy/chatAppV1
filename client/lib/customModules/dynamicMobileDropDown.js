var mobileDropDowns={};
var mobDropDownCount=0;
//
//SearchPaginateHook is a function which will be triggered with the search keyword & page number which can be triggered
//                   when user either searches something on the search bar or keeps scrolling down - pagination
//                   Hence two inputs to the function - searchText & pageNo. Note than searchText can be passed null
//parentContainer is DOM node of the parent node in which drop down has to be populated
function loadModuleTemplate(href)
{
    if(href)
    {
        var xmlhttp = new XMLHttpRequest();
        let moduleLocation="./lib/customModules/";
        xmlhttp.open("GET", moduleLocation+href, false);
        xmlhttp.send();
        return xmlhttp.responseText;
    }
    else
    {
        return "Module not registered";
    }
  
}
document.body.innerHTML+=loadModuleTemplate("dynamicMobileDropDown.html");
class dynamicMobileDropDown{
    constructor(dropOptions,searchHook,parentContainer){
        this.dropOptions=dropOptions;
        this.searchHook=searchHook;
        this.parentContainer=parentContainer;
        this.selectedText=null;
        this.templates=document.getElementById("mobileDropDownTemplates");
        var that=this;
        if(this.templates)
        {
            this.dropDownTextElem=this.templates.querySelector("#mobileDropTextElem").cloneNode(true); 
            this.dropDownBody=this.templates.querySelector("#mobileDropDownBody").cloneNode(true);
            this.dropOptionTemplate=this.templates.querySelector("#mobileDropOptions");
            this.dropOptionsContainer=this.dropDownBody.querySelector("#dropItemsContainer");
            this.dropDownSearchElement=this.dropDownBody.querySelector("#searchText");
            this.dropItemsContainer=this.dropDownBody.querySelector("#dropItemsContainer");
        }
        this.parentContainer.appendChild(this.dropDownTextElem);
        this.dropDownTextElem.addEventListener("click",()=>{that.showDropDownBody(that);});
        this.dropDownBody.classList.add("hide");
        document.body.appendChild(this.dropDownBody);
        this.dropDownBody.id+=`${mobDropDownCount}`;
        this.dropDownTextElem.id+=`${mobDropDownCount}`;
        this.dropOptionsContainer.id+=`${mobDropDownCount}`;
        this.dropDownSearchElement.id+=`${mobDropDownCount}`;
        this.dropDownSearchElement.addEventListener("keydown",()=>{
            that.searchDebounce(that);
        });
        this.debounceTimer=null;
        this.currentPage=0;
        this.refreshDropDown(this.dropOptions);
        this.dropOptionsContainer.addEventListener("scroll",()=>{
            that.infiniteScroll(that);
        });
        this.currentSearchStr=null;
        mobDropDownCount++;
    }
    destroyDependencies()
    {
        console.log("Inside destructor");
        this.dropDownBody.innerHTML='';
        this.dropDownBody.remove();
    }
    showDropDownBody(objRef)
    {
        //show the drop down body
        console.log("drop down clicked")
        objRef.dropDownBody.classList.remove("hide");
    }
    closeDropDownBody()
    {
        this.dropDownBody.classList.add("hide");
    }
    getDropOptions()
    {
        return this.dropOptions;
    }
    setDropOptions(dropItems)
    {
        this.dropOptions=dropItems;
    }
    refreshDropDown(dropItems)
    {
        this.setDropOptions(dropItems);
        this.clearDropOptions();
        this.addDropItems(dropItems);
    }
    addDropItems(dropItems)
    {
        for(let option of dropItems)
        {
            let dropOptionClone=this.templates.querySelector("#mobileDropOptions").cloneNode(true);
            let that=this;
            dropOptionClone.innerHTML=option;
            if(option==this.selectedText)
            {
                dropOptionClone.classList.add("drop-text-selected");
            }
            this.dropOptionsContainer.appendChild(dropOptionClone);
            dropOptionClone.addEventListener("click",()=>{
            that.setDropOption(dropOptionClone);
            });
        }
    }
    setDropOption(dropOptionItem)
    {
        let dropSelectElem=this.dropDownTextElem.querySelector("#dropDownSelectText");
        this.selectedText=dropOptionItem.innerHTML;
        dropSelectElem.innerHTML=this.selectedText;
        let dropOptions=this.dropOptionsContainer.querySelectorAll("#mobileDropOptions");
        for(let option of dropOptions)
        {
            option.classList.remove("drop-text-selected");
        }
        dropOptionItem.classList.add("drop-text-selected");
        this.closeDropDownBody();
    }
    clearDropOptions()
    {
        this.dropOptionsContainer.innerHTML='';
    }
    //write search and pagination
    searchDebounce(ObjRef)
    {
        let searchLoader=ObjRef.templates.querySelector("#searchLoader").cloneNode(true);
        if(ObjRef.debounceTimer)
        {
            clearTimeout(ObjRef.debounceTimer);
            ObjRef.debounceTimer=setTimeout(()=>{
                ObjRef.currentPage=0;
                ObjRef.currenSearchStr=ObjRef.dropDownSearchElement.value;
                ObjRef.dropOptionsContainer.innerHTML=``;
                ObjRef.dropOptionsContainer.appendChild(searchLoader);
                ObjRef.searchHook(ObjRef.dropDownSearchElement.value,ObjRef.currentPage);
                ObjRef.debounceTimer=null;
            },250);
        }
        else
        {
            ObjRef.debounceTimer=setTimeout(()=>{
                ObjRef.currentPage=0;
                ObjRef.currenSearchStr=ObjRef.dropDownSearchElement.value;
                ObjRef.searchHook(ObjRef.dropDownSearchElement.value,ObjRef.currentPage);
                ObjRef.debounceTimer=null;
            },250);
        }
    }
    //infiniteScrolling
    infiniteScroll(ObjRef)
    {
        if(ObjRef.dropOptionsContainer.scrollTop+ObjRef.dropOptionsContainer.offsetHeight>=ObjRef.dropOptionsContainer.scrollHeight)
        {
            ObjRef.currentPage++;
            console.log("Page Loading");
            let scrollLoaderClone=ObjRef.templates.querySelector("#scrollLoader").cloneNode(true);
            ObjRef.dropOptionsContainer.appendChild(scrollLoaderClone);
            ObjRef.searchHook(ObjRef.currenSearchStr,ObjRef.currentPage);
            scrollLoaderClone.remove();
        }
    }

}