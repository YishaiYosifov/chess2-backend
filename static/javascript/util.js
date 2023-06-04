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
        console.log(123);
        
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
    authInfo = await getLocalStorage("auth-info", {});
    if (["/login", "/signup"].includes(location.pathname) || Object.keys(authInfo).length) return;

    const request = await apiRequest("/profile/me/get_info", {"include": ["user_id", "auth_method"]});
    if (!request.ok) {
        if (request.status == 401) return;
        window.location.replace("/api/auth/logout");
    }

    authInfo = await request.json();
    localStorage.setItem("auth-info", JSON.stringify(authInfo));
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