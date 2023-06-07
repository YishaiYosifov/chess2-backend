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