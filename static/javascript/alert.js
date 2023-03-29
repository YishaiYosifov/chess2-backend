const alertHTML = $($.parseHTML(`
    <div class="container">
        <div class="alert alert-info alert-dismissible fade show" role="alert" id="alert">
            <div id="alertText" style="white-space: pre-wrap;"></div>
            <button class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    </div>
`))

message = document.currentScript.getAttribute("alert");
window.addEventListener("load", () => {
    if (message == "None") return;

    const alertText = alertHTML.find("#alertText");
    alertText.html(message);

    if ($(".navbar").length) $("body").insertAfter(".navbar");
    else $("body").prepend(alertHTML);
});