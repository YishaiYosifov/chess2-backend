var userInfo = {}

async function main() {
    userInfo = await (await apiRequest(`/profile/${window.location.pathname.split("/").pop()}/get_info`)).json();
    $("#profile-picture").prop("src", `/static/uploads/${userInfo["member_id"]}/profile-picture.jpeg`);

    let username = $("#username-group")
    let usernameText = $(`<span id="username" data-bs-placement="left">${userInfo["username"]}</span>`);
    usernameText.attr("title", userInfo["username"])
    username.append(usernameText);
    new bootstrap.Tooltip(usernameText);

    country = $("#country")
    country.attr("title", userInfo["country"]);
    new bootstrap.Tooltip(country);
    country.prop("src", `/assets/country/${userInfo["country_alpha"]}`)

    $("#about").text(userInfo["about"])
}
main();