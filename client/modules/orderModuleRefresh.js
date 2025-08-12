
function populateOrders(parentId,orders)
{
    let orderModuleTemplates=document.getElementById("orderModuleTemplates");
    let parentEle=document.getElementById(parentId);
    if(orderModuleTemplates && parentEle)
    {
        let orderCard=orderModuleTemplates.querySelector("#orderCard");
        if(orderCard)
        {
            parentEle.innerHTML='';
            for(let order of orders)
            {
                let orderCardClone=orderCard.cloneNode(true);
                let orderCardHeader=orderCardClone.querySelector("#cardHeader");
                let orderCardStatus=orderCardClone.querySelector("#orderStatus");
                let orderCardCreatedDate=orderCardClone.querySelector("#orderCreatedDate");
                let orderStatusHTML=order.status;
                let successIcon=orderModuleTemplates.querySelector("#fullfilledIcon").cloneNode(true);
                let failureIcon=orderModuleTemplates.querySelector("#failedIcon").cloneNode(true);
                let intermediateIcon=orderModuleTemplates.querySelector("#underProcessIcon").cloneNode(true);
                let clockIcon=orderModuleTemplates.querySelector("#clockIcon").cloneNode(true);
                orderCardHeader.innerHTML=order.name;
                if(order.status.includes("Fullfil"))
                {
                    orderCardStatus.appendChild(successIcon);
                }
                else if(order.status.includes("Under Process"))
                {
                    orderCardStatus.appendChild(intermediateIcon);
                }
                else
                {
                    orderCardStatus.appendChild(failureIcon);
                }
                orderCardCreatedDate.appendChild(clockIcon);
                orderCardStatus.innerHTML+=order.status;
                orderCardCreatedDate.innerHTML+=order.createDate;
                parentEle.appendChild(orderCardClone);
            }
        }
    }
    
}
function loadOrders()
{
    //Hit the API here - cache
    let prePlannedOrders=[
        {
            name:"Order 1",
            createDate:"20-03-2025",
            status:"Last Fullfilled 21-03-2025"
        },
        {
            name:"Order 2",
            createDate:"20-03-2025",
            status:"Under Process"
        },
        {
            name:"Order 3",
            createDate:"20-03-2025",
            status:"Under Process"
        }
    ];
    let myOrders=[
        {
            name:"Order 1",
            createDate:"20-03-2025",
            status:"Fullfilled 21-03-2025"
        },
        {
            name:"Order 2",
            createDate:"20-03-2025",
            status:"Under Process"
        },
        {
            name:"Order 3",
            createDate:"20-03-2025",
            status:"Under Process"
        }
    ];
    populateOrders("plannedOrderParent",prePlannedOrders);
    populateOrders("myOrderParent",myOrders);
}
loadOrders();