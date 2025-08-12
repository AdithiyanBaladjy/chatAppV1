qrScanner=new Html5QrcodeScanner("reader",{fps:10},false);
qrScanner.render(onScanSuccess,onScanFailure);