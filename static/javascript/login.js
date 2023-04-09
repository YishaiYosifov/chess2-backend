$("#login").click(async () => {
    var selector = $("#selector").val();
    var password = $("#password").val();

    var response = await apiRequest("/auth/login", {selector: selector, password: password});
    if (!response.ok) error("Wrong username / password");
    else window.location.replace("/");
});

async function error(message) {
    var error = $("<div>", {class: "rounded bg-danger mb-2", text: message});
    error.hide();
    error.appendTo($("#errors"));

    error.fadeIn(200)
    await sleep(3000)
    error.fadeOut(200)
}