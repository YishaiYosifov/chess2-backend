//#region Alert

const alertHTML = $($.parseHTML(`
    <div class="container mt-3 col-md-5 mx-auto alert alert-dismissible fade show text-center" style="display: none;" role="alert">
        <div id="alertText" style="white-space: pre-wrap;"></div>
        <button class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
`))

const URLAlerts = {
    "session-expired": {"urls": ["/login"], "message": "Your session expired, please log in again!", color: "danger"},
    "settings_updated": {"urls": ["/settings"], "message": "Updated!", color: "success"},
    "password_updated": {"urls": ["/settings"], "message": "Password Updated!", color: "success"}
}

var message = document.currentScript.getAttribute("alert").replaceAll("'", "\"");
window.addEventListener("load", () => {
    var urlMessage = new URLSearchParams(location.search).get("a")
    if (urlMessage) {
        if (!(urlMessage in URLAlerts)) return;

        const alertData = URLAlerts[urlMessage];
        if (!window.location.pathname.includes(alertData["urls"])) return;

        message = alertData["message"];
        var color = alertData["color"]

        window.history.replaceState({}, null, window.location.pathname.split("/").pop())
    }
    else if (message == "None") return;
    else {
        let messageData = JSON.parse(message);
        message = messageData["message"];
        var color = messageData["color"]
    }

    showAlert(message, color);
});

function showAlert(message, color="danger") {
    $(".alert").remove();

    let alertObject = alertHTML.clone();
    alertObject.addClass(`alert-${color}`)
    let alertText = alertObject.find("#alertText");
    alertText.text(message);

    if ($(".navbar").length) alertObject.insertAfter(".navbar");
    else $("body").prepend(alertObject);
    alertObject.fadeIn(300);
}

//#endregion

//#region Password Confirmation

async function confirmPassword() {
    $("#password-confirmation").modal("show");

    return await new Promise((resolve) => {
        $("#password-confirmation-submit").click(resolve)
    }).then(() => { return $("#password").val(); });
}

//#endregion