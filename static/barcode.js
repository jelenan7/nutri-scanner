let html5Qr = new Html5Qrcode("reader");

const scannerBox = document.getElementById("reader");
const scanMsg = document.getElementById("scan-message");

function clearScanMessage() {
    scanMsg.textContent = "";
    scanMsg.classList.remove("scan-message--error");
}

function handleScanSuccess(decodedText) {
    const input = document.getElementById("barcode");
    const form = document.getElementById("barcode-form");

    input.value = decodedText;
    form.submit();
}

/* START CAMERA */
document.getElementById("open-camera").onclick = async () => {
    clearScanMessage();
    scannerBox.classList.remove("show-gif");

    try {
        const devices = await Html5Qrcode.getCameras();
        await html5Qr.start(
            devices[0].id,
            { fps: 10, qrbox: 200 },
            handleScanSuccess
        );
    } catch (err) {
        scanMsg.textContent = "Camera cannot start.";
        scanMsg.classList.add("scan-message--error");
        scannerBox.classList.add("show-gif");
    }
};

/* UPLOAD IMAGE */
document.getElementById("upload-image").onclick = () => {
    document.getElementById("file-input").click();
};

document.getElementById("file-input").onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    clearScanMessage();
    scannerBox.classList.remove("show-gif");

    try {
        await html5Qr.scanFile(file, true).then(handleScanSuccess);
    } catch (err) {
        scanMsg.innerHTML = `
            ❌ No barcode found in the image.<br>
            🔄 Refreshing in 3 seconds...
        `;
        scanMsg.classList.add("scan-message--error");
        scannerBox.classList.add("show-gif");

        // Refresh after 3 seconds
        setTimeout(function () {
            window.location.reload();
        }, 3000);
    }
};
