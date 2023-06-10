async function apiRequest(route, json=null) {
    const csrfToken = $("[name='csrf_token']").val();
    const response = await fetch(`/api${route}`, {
            method: "POST",
            body: JSON.stringify(json),
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            }
        }
    );

    if (Object.keys(authInfo).length && authInfo["auth_method"] != "guest" && response.status == 401 && await response.clone().text() == "Not Logged In") {
        localStorage.removeItem("auth-info");
        
        window.location.replace("/login?a=session-expired");
        throw new Error("Session Token Expired");
    }
    
    return response;
}

async function apiUpload(route, name, file) {
    const csrfToken = $("[name='csrf_token']").val();

    const data = new FormData();
    data.append(name, file);
    return await fetch(`/api${route}`, {
        method: "POST",
        body: data,
        headers: {
            "X-CSRFToken": csrfToken
        }
    });
}

function getLocalStorage(name, _default) {
    value = localStorage.getItem(name);
    if (!value) return _default;

    try { value = JSON.parse(value); }
    catch (e) {}
    return value;
}

function decodeFlaskCookie(value) {
    if (value.indexOf("\\") == -1) return value;

    value = value.slice(1, -1).replace(/\\"/g, '"');
    value = value.replace(/\\(\d{3})/g, (match, octal) => String.fromCharCode(parseInt(octal, 8)));
    return value.replace(/\\\\/g, '\\');
}
async function getCookie(name, _default) {
    const cookies = document.cookie.split(";");
    for(var i = 0; i < cookies.length; i++) {
        let [cookieName, cookieValue] = cookies[i].trim().split("=");
        if (cookieName.startsWith(name)) {
            try { cookieValue = JSON.parse(decodeFlaskCookie(cookieValue)); }
            catch (e) {}
            return cookieValue;
        }
    }
    return _default;
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

function togglePasswordVisibility(toggleButton) {
    toggleButton = $(toggleButton);
    var icon = toggleButton.children("i");
    var input = $(toggleButton.attr("password-input"));

    if (icon.hasClass("bi-eye-slash-fill")) {
        input.attr("type", "password");

        icon.addClass("bi-eye-fill");
        icon.removeClass("bi-eye-slash-fill");
    } else {
        input.attr("type", "text");

        icon.addClass("bi-eye-slash-fill");
        icon.removeClass("bi-eye-fill");
    }
};

function isDigit(text) { return /^\d+$/.test(text); }

var authInfo;
async function loadAuthInfo() {
    authInfo = await getCookie("auth_info", {})
    if (!authInfo) {
        window.location.replace("/logout");
        return;
    }
    return authInfo;
}
loadAuthInfo();

const percent = (num, whole) => (num * whole) / 100

function formatSeconds(seconds) {
    if (seconds < 0) return "0:00.0";
    if (Math.abs(seconds - Math.round(seconds)) < 0.1) seconds = Math.round(seconds);
    
    minutes = Math.floor(seconds / 60);
    seconds -= minutes * 60;
    seconds = seconds.toFixed(1);

    seconds = seconds.toString();
    if (seconds.split(".")[0].length == 1) seconds = "0" + seconds;
    return `${minutes}:${seconds}`;
}

numToLetter = num => String.fromCharCode(97 + num);

class PromiseQueue {
    constructor() {
        this.queue = [];
        this.promise;
    }

    add(task) {
        if (!this.promise) this._createPromise(task);
        else this.queue.push(task);
        return this;
    }

    _createPromise(task) {
        this.promise = new Promise(task).then(() => {
            task = this.queue.shift();

            if (!task) {
                this.promise = null;
                return;
            }
            this._createPromise(task);
        });
    }

    get isActive() { return this.queue.length > 0 || this.promise != null; }
}

//#region Alert

const alertHTML = $($.parseHTML(`
    <div class="container mt-3 col-md-5 mx-auto alert alert-dismissible fade show text-center" style="display: none;" role="alert">
        <div id="alertText" style="white-space: pre-wrap;"></div>
        <button class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
`))

const URLAlerts = {
    "session-expired": {"urls": ["/login"], "message": "Your session expired, please log in again!", color: "danger"},
    "settings-updated": {"urls": ["/settings"], "message": "Updated!", color: "success"},
    "password-updated": {"urls": ["/settings"], "message": "Password Updated!", color: "success"},
    "account-deleted": {"urls": ["/"], "message": "Your account has been deleted.", color: "warning"}
}

function triggerAlert() {
    const serverMessage = $("script").last().attr("alert").replaceAll("'", "\"");
    const urlMessage = new URLSearchParams(location.search).get("a");

    let messageText;
    let color;
    if (urlMessage) {
        if (!(urlMessage in URLAlerts)) return;

        const alertData = URLAlerts[urlMessage];
        if (!window.location.pathname.includes(alertData["urls"])) return;

        messageText = alertData["message"];
        color = alertData["color"];

        let pathname = window.location.pathname.split("/").pop();
        pathname = (pathname == "") ? "/" : pathname;
        window.history.replaceState({}, null, pathname);
    }
    else if (serverMessage == "None") return;
    else {
        let messageData = JSON.parse(serverMessage);
        messageText = messageData["message"];
        color = messageData["color"];
    }

    showAlert(messageText, color);
}
triggerAlert()

function showAlert(message, color="danger") {
    $(".alert").remove();

    const alertObject = alertHTML.clone();
    alertObject.addClass(`alert-${color}`)
    alertObject.find("#alertText").text(message);

    if ($("#alert-wrapper").length) $("#alert-wrapper").append(alertObject);
    else if ($(".navbar").length) alertObject.insertAfter(".navbar");
    else $("body").prepend(alertObject);

    alertObject.fadeIn(300);
}

//#endregion

//#region Password Confirmation

async function confirmPassword() {
    $("#password-confirmation").modal("show");

    return await new Promise((resolve) => $("#password-confirmation-submit").click(resolve))
                                .then(() => $("#password").val());
}

//#endregion

//#region Navbar

const navbar = $($.parseHTML(`
    <nav class="navbar navbar-expand-lg">
        <div class="container-fluid">
            <button class="navbar-toggler shadow-none text-white border-0 align-items-center d-flex d-lg-none" type="button" data-bs-toggle="offcanvas" data-bs-target="#navbarOffcanvas" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle offcanvas">
                <i class="bi bi-list" style="font-size: 50px;"></i>
                <a class="navbar-brand text-white">Chess 2</a>
            </button>
            <div class="collapse navbar-collapse navbar-top">
                <ul class="navbar-nav">
                    <a class="navbar-brand" style="color: #99999a;" href="/">Chess 2</a>

                    <li class="nav-item" id="navbar-seperator">
                        <a class="nav-link">|</a>
                    </li>
                </ul>
            </div>
        </div>
        <div class="offcanvas offcanvas-start d-flex d-lg-none" tabindex="-1" id="navbarOffcanvas" aria-labelledby="navbarOffcanvas" style="background-color: #687c8b;">
            <div class="offcanvas-header">
                <a href="/" class="nav-link offcanvas-title">
                    <h5>
                        <img src="/static/assets/logo.webp" alt="Logo" width="30" height="30" class="d-inline-block align-text-top rounded">
                        <b>Chess 2</b>
                    </h5>
                </a>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas" aria-label="Close"></button>
            </div>
            <div class="offcanvas-body">
                <ul class="navbar-nav justify-content-end flex-grow-1 pe-3" id="offset-top">
                </ul>
                <ul class="navbar-nav justify-content-end flex-grow-1 pe-3" id="offset-bottom">
                    <hr style="background-color: black;">
                </ul>
            </div>
        </div>
    </nav>`
));

const navItem = $($.parseHTML(`
    <li class="nav-item">
        <a class="nav-link">
            <i class="bi"></i>
        </a>
    </li>
`))

function createNavbar(navbarItems) {
    const isLoggedIn = Object.keys(authInfo).length && authInfo["auth_method"] != "guest";

    const offsetTop = navbar.find("#offset-top");
    const offsetBottom = navbar.find("#offset-bottom");
    const navbarSeperator = navbar.find("#navbar-seperator");
    for (const item of navbarItems) {
        if ((item["auth_req"] == 1 && !isLoggedIn) ||
            (item["auth_req"] == 2 && isLoggedIn)) continue;

        const navItemTemplate = navItem.clone();
        const navText = navItemTemplate.find("a");
        if (item["path"] == window.location.pathname.split("/")[1]) navText.addClass("active");

        navText.attr("href", `${location.protocol}//${location.host}/${item["path"]}` );
        navText.find("i").addClass(item["icon"])

        navText.append(item["label"])

        if (item["side"] == "top") {
            offsetTop.append(navItemTemplate.clone());
            navItemTemplate.insertBefore(navbarSeperator);
        }
        else {
            offsetBottom.append(navItemTemplate.clone());
            navItemTemplate.insertAfter(navbarSeperator);
        }
    };
    $("body").prepend(navbar);
}

loadAuthInfo().then(() => {
    const root = location.protocol + "//" + location.host
    $.getJSON(`${root}/static/navbar.json`, createNavbar)
});

//#endregion