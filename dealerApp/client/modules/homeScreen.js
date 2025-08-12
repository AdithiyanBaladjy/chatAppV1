function homeMenuClick(btnElem,menuName)
{
    let btns=btnElem.parentNode.children;
    for(let btn of btns)
    {
        btn.classList.remove("selected-icon-container");
    }
    btnElem.classList.add("selected-icon-container");

    loadModule(menuName,"homeScreenMenuParent");
}