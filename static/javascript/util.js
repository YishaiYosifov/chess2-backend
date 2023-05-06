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
    if (responseCopy.status == 401 && await responseCopy.text() == "Session Expired") {
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

async function setCookie(name, value, expires) { document.cookie = `${name}=${value || ""}; path=/; SameSite=Lax; max-age=${expires}`; }

async function getCookie(name) {
    var cookies = document.cookie.split(";");
    for(var i=0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.startsWith(name)) return cookie.split("=")[1];
    }
}

async function eraseCookie(name) { document.cookie = name + "=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT; SameSite=Lax"; }

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

document.querySelectorAll(".tt").forEach(tooltip => new bootstrap.Tooltip(tooltip));