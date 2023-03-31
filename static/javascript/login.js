$("#login").click(async () => {
    var selector = $("#selector").val();
    var password = $("#password").val();

    const response = await apiRequest("login", {selector: selector, password: password});
    if (!response.ok) error("Wrong username / password");
    else window.location.replace("/");
});

var passwordVisible = false;
$("#passwordToggle").click(() => {
    var icon = $("#passwordToggleIcon")
    var input = $("#password")

    if (passwordVisible) {
        input.attr("type", "password");

        icon.addClass("bi-eye-fill");
        icon.removeClass("bi-eye-slash-fill");
    } else {
        input.attr("type", "text");

        icon.addClass("bi-eye-slash-fill");
        icon.removeClass("bi-eye-fill");
    }
    passwordVisible = !passwordVisible;
});

async function error(message) {
    var error = $("<div>", {class: "rounded bg-danger mb-2", text: message});
    error.hide();
    error.appendTo($("#errors"));

    error.fadeIn(200)
    await sleep(3000)
    error.fadeOut(200)
}