const alertHTML = $($.parseHTML(`
    <div class="container mt-3">
        <div class="alert alert-info alert-dismissible fade show" role="alert" id="alert">
            <div id="alertText" style="white-space: pre-wrap;"></div>
            <button class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    </div>
`))

const URLAlerts = {
    "session-expired": {"urls": ["/login"], "message": "Your session expired, please log in again!"}
}

message = document.currentScript.getAttribute("alert");
window.addEventListener("load", () => {
    if (urlMessage = new URLSearchParams(location.search).get("a")) {
        if (!(urlMessage in URLAlerts)) return;

        const alertData = URLAlerts[urlMessage];
        if (!window.location.pathname.includes(alertData["urls"])) return;
        message = alertData["message"];
    }
    else if (message == "None") return;

    const alertText = alertHTML.find("#alertText");
    alertText.html(message);

    if ($(".navbar").length) $("body").insertAfter(".navbar");
    else $("body").prepend(alertHTML);
});