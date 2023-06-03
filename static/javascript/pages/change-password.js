function showError(target, text) {
    const error = $(`#${target}-error`);
    error.text(text);
    error.fadeIn(200);
}
function hideErrors() { $("[id$=-error").fadeOut(200); }

$("#update").click(async () => {
    hideErrors();

    let currentPassword = $("#current-password").val();
    let newPassword = $("#new-password").val();
    let retype = $("#retype-password").val();
    if (newPassword != retype) {
        showError("retype-password", "Passwords don't match!");
        return;
    }

    const response = await apiRequest("/profile/me/update", {"password": newPassword, password_confirmation: currentPassword});
    if (response.status == 401) {
        showError("current-password", "Incorrect Password");
        return;
    }
    else if (response.status == 400) {
        showError("new-password", "Your password must be at least 8 characters long, have both lower and upper case letters and include a number.")
        return;
    }
    else if (response.status == 500) {
        showAlert("Something went wrong.");
        return
    } else if (!response.ok) {
        showAlert(await response.text());
        return;
    }

    window.location.replace("/settings?a=password-updated");
    console.log(await response.text());
});