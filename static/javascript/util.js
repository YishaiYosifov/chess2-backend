async function apiRequest(route, json=null) {
    var response = await fetch(`/api${route}`, {
            method: "POST",
            body: JSON.stringify(json),
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        }
    );

    var responseCopy = response.clone();
    if (authInfo["auth_method"] != "guest" && responseCopy.status == 401 && await responseCopy.text() == "Session Expired") {
        window.location.replace("/login?a=session-expired");
        throw new Error("Session Token Expired");
    }
    
    return response;
}

async function apiUpload(route, name, file) {
    let data = new FormData();
    data.append(name, file);
    return await fetch(`/api${route}`, {
        method: "POST",
        body: data
    });
}

function getLocalStorage(name, _default) {
    value = localStorage.getItem(name);
    if (!value) return _default;

    try { value = JSON.parse(value); }
    catch (e) {}
    return value;
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

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
    if (Object.keys(authInfo).length) return;

    const request = await apiRequest("/profile/me/get_info", {"include": ["user_id", "auth_method"]});
    if (!request.ok) {
        if (request.status == 401) return;
        window.location.replace("/api/auth/logout");
    }

    authInfo = await request.json();
    localStorage.setItem("auth-info", JSON.stringify(authInfo));
}
loadAuthInfo();