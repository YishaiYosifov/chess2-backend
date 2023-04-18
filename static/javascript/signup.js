const tooltips = document.querySelectorAll(".tt")
tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));

function showError(target, text) {
    const error = $(`#${target}Error`);
    error.text(text);
    error.fadeIn(200);
}

function hideError(target) { $(`#${target}Error`).fadeOut(200); }

function isPasswordValid(password, allowEmpty = false) {
    const passwordReg = /^(?=.*[A-Z])(?=.*)(?=.*[0-9])(?=.*[a-z]).{8,}$/g;
    if ((allowEmpty && !password) || passwordReg.exec(password)) {
        hideError("password");
        return Boolean(password);
    }
    showError("password", "• Invalid Password!");
    return false;
}
function isEmailValid(email, allowEmpty = false) {
    const emailReg = /[\w\.-]+@[\w\.-]+(\.[\w]+)+/g;
    if ((allowEmpty && !email) || emailReg.exec(email)) {
        hideError("email");
        return Boolean(email);
    }
    showError("email",  "• Invalid Email!")
    return false;
}
async function isUsernameValid(username) {
    if (!username) {
        showError("username", "• Username is required!");
        return false;
    } else if (username.length >= 30) {
        showError("username", "• Username too long!");
        return false;
    } else if (username.includes(" ")) {
        showError("username", "Username can't include a space!");
        return;
    }
    hideError("username");
    return true;
}

$("#password").on("input", () => { isPasswordValid($("#password").val(), true); });

$("#email").on("input", () => { isEmailValid($("#email").val(), true); });

$("#username").on("input", () => { isUsernameValid($("#username").val()); })

$("#signup").click(async () => {
    const username = $("#username").val();
    const email = $("#email").val();
    const password = $("#password").val();

    if (!await isUsernameValid(username) || !isEmailValid(email) || !isPasswordValid(password)) return;

    var response = await apiRequest("/auth/signup", {"username": username, "email": email, "password": password})
    if (response.status == 409) {
        reason = await response.text();
        console.log(reason)
        if (reason == "Username Taken") showError("username", "• Username Taken!");
        else showError("email", "• Email Taken!");
        return;
    }
    else if (response.status == 500) {
        showAlert("Something went wrong.");
        return;
    }
    else if (!response.ok) {
        showAlert(await response.text());
        return;
    }
    hideError("signup");
    window.location.replace("login")
});