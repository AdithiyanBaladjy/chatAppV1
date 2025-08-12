console.log("Static js files are served correctly");
function check_input(input_elem,label_id)
{
    if(input_elem.value=='')
    {
        document.getElementById(label_id).classList.add('fly-label');
    }
    else
    {
        document.getElementById(label_id).classList.remove('fly-label');
    }
}

function sign_in()
{
    window.location.href="/static/chat_home.html";
}