$("#login").click(async () => {
    var selector = $("#selector").val();
    var password = $("#password").val();

    var response = await apiRequest("/auth/login", {selector: selector, password: password});
    if (!response.ok) showAlert("Wrong username / password");
    else window.location.replace("/");
});

localStorage.removeItem("auth-info");