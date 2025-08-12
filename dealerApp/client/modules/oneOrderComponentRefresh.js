productDropDownParent=document.getElementById("productDropDownParent");
originalProductsList=["Residential Pump","Solar Pump","Wires","Cables","Residential Pump","Solar Pump","Wires","Cables","Residential Pump","Solar Pump","Wires","Cables","Residential Pump","Solar Pump","Wires","Cables","Residential Pump","Solar Pump","Wires","Cables"];
productDropDown=new dynamicMobileDropDown(originalProductsList,(searchText,pageNo)=>{
productSearch(searchText,pageNo)
},productDropDownParent);

function productSearch(searchText,pageNo)
{
    console.log("Inside search hook",searchText,pageNo);
    let results=getProducts(searchText,pageNo);
    if(pageNo>0)
    {
        productDropDown.addDropItems(results);
    }
    else
    {
        productDropDown.refreshDropDown(results);
    }
}

function getProducts(searchText,pageNo)
{
    let perPage=50;
    let outArr=[];
    if(pageNo==0)
    {
        if(searchText==null || searchText == '')
        {
            outArr=originalProductsList;
        }
        else
        {
            for(let product of originalProductsList)
            {
                if(product.toLowerCase().includes(searchText.toLowerCase()))
                {
                    outArr.push(product);
                }
            }
        }
        
    }
    else
    {
        for(let i=pageNo;i<pageNo+perPage;i++)
        {
            outArr.push(`Pump ${i}`);
        }
    }
    return outArr;
}