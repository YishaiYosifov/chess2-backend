const gameHTML = $($.parseHTML(
    `<tr>
        <td><img class="mt-2" id="mode-image" style="width: 60px; height: 60px;" alt="Anarchy" data-bs-placement="top"></td>
        <td class="fs-6">
            <p class="mt-2 limit-text" id="white-username" style="width: 150px; cursor: pointer;"></p>
            <p class="text-black limit-text" id="black-username" style="width: 150px; cursor: pointer;"></p>
        </td>
        <td>
            <div class="float-start text-center text-white-50 fs-6" style="line-height: 0.1; margin-top: 23px;">
                <p id="white-wins"></p>
                <p>-</p>
                <p id="black-wins"></p>
            </div>
            <i class="bi d-flex ms-3 float-start" id="results" style="font-size: 40px; margin-top: 23px;"></i>
        </td>
    </tr>`
));

var userInfo = {};

async function main() {
    const username = window.location.pathname.split("/").pop();

    userInfo = await (await apiRequest(`/profile/${username}/get_info`)).json();
    $("#profile-picture").prop("src", `/static/uploads/${userInfo["member_id"]}/profile-picture.jpeg`);

    let usernameGroup = $("#username-group");
    let usernameText = $(`<span id="username limit-text" data-bs-placement="left" style="width: 280px;">${userInfo["username"]}</span>`);
    usernameText.attr("title", userInfo["username"]);
    usernameGroup.append(usernameText);
    new bootstrap.Tooltip(usernameText);

    country = $("#country");
    country.attr("title", userInfo["country"]);
    new bootstrap.Tooltip(country);
    country.prop("src", `/assets/country/${userInfo["country_alpha"]}`);

    $("#about").text(userInfo["about"]);

    const games = await (await apiRequest(`/profile/${username}/get_games`, {"limit": 10})).json();
    if (games.length) {
        const gamesTable = $("#games");
        gamesTable.show();

        const tableBody = gamesTable.find("tbody")
        for (const game of games) {
            let gameElement = gameHTML.clone();

            let whiteUsername = gameElement.find("#white-username");
            whiteUsername.text(game["white"]);
            if (game["white"] != "DELETED") whiteUsername.attr("onclick", `window.location.replace("/member/${game["white"]}")`);

            let blackUsername = gameElement.find("#black-username");
            blackUsername.text(game["black"]);
            if (game["black"] != "DELETED") blackUsername.attr("onclick", `window.location.replace("/member/${game["black"]}")`);

            let modeImage = gameElement.find("#mode-image");
            modeImage.prop("src", `../static/assets/modes/${game["mode"]}.png`);
            modeImage.prop("title", game["mode"]);
            new bootstrap.Tooltip(modeImage);

            gameElement.find("#white-wins").text(game["white_wins"]);
            gameElement.find("#black-wins").text(game["black_wins"]);

            let results =  gameElement.find("#results");
            if ((game["winner"] == "white" && game["white"] == username) ||
                (game["winner"] == "black" && game["black"] == username)) {
                results.addClass("bi-plus-square");
                results.addClass("text-success");
            }
            else {
                results.addClass("bi-dash-square");
                results.addClass("text-danger");
            }

            tableBody.append(gameElement);
        }

    } else $("#no-games").show();
}
main();

function setProfilePirctureSize() {
    let picture = $("#profile-picture");
    picture.height(picture.width());
}