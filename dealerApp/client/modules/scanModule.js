function onScanSuccess(decodedText,decodedResult)
{
    console.log("Scan results",decodedText,decodedResult);
    document.getElementById("scannedOut").innerHTML=decodedText;
    // document.getElementById(`html5-qrcode-button-camera-stop`).click();
}
function onScanFailure(err)
{
    console.error("Scan error: ",err);
}
