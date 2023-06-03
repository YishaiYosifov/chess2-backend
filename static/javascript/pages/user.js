google.charts.load("current", {packages: ["corechart"]});

const gameHTML = $($.parseHTML(
    `<tr class="col-11 text-start" style="cursor: pointer;">
        <td>
            <img class="img-fluid mt-2 border border-3 rounded-circle" id="mode-image" style="min-width: 60px; min-height: 60px; max-width: 60px; max-height: 60px" alt="Mode" data-bs-placement="top">
        </td>
        <td class="fs-6">
            <p class="mt-2 limit-text" id="white-username" style="width: 130px; cursor: pointer;"></p>
            <p class="text-secondary limit-text" id="black-username" style="width: 130px; cursor: pointer;"></p>
        </td>
        <td>
            <div class="float-start text-center text-white-50 fs-6" style="line-height: 0.1; margin-top: 23px;">
                <p id="white-wins"></p>
                <p>-</p>
                <p id="black-wins"></p>
            </div>
            <i class="bi d-flex ms-3 float-start" id="results" style="font-size: 20px; margin-top: 30px;"></i>
        </td>
    </tr>`
));

const ratingHTML = $($.parseHTML(
    `<div class="card text-white border-0 rounded-0 col-11 col-sm-8 col-md-5 col-xl-4 col-xxl-3" style="max-width: 470px; background-color: var(--dark-secondary)">
        <div class="card-header text-start">
            <img id="rating-image" class="img-fluid rounded-circle border border-3" style="width: 30px; height: 30px">
            <span class="ms-2" id="rating-mode"></span>

            <span class="text-white" id="elo" style="float: right;">800</span>
        </div>
        <div class="card-body text-start">
            <div class="mx-auto chart mb-3" style="width: 100%;"></div>

            <p class="text-white-50" style="float: left; width: 230px;">Higest</p>
            <span id="rating-highest" style="color: var(--soft-green); float: left;"></span>

            <div style="clear: both"></div>

            <p class="text-white-50" style="float: left; width: 230px;">Lowest</p>
            <span class="text-danger" id="rating-lowest" style="float: left;"></span>

            <div style="clear: both"></div>

            <p class="text-white-50" style="float: left; width: 230px;">Rating Change (last month)</p>
            <span id="rating-change" style="float: left;"></span>
            </div>
        </div>
    </div>`
));

var userInfo = {};

async function main() {
    const username = window.location.pathname.split("/").pop();

    userInfo = await (await apiRequest(`/profile/${username}/get_info`)).json();
    $("#profile-picture").prop("src", `/static/uploads/${userInfo.user_id}/profile-picture.jpeg`);

    let usernameGroup = $("#username-group");
    let usernameText = $(`<span id="username limit-text" data-bs-placement="left" style="width: 280px;">${userInfo.username}</span>`);
    usernameText.attr("title", userInfo.username);
    usernameGroup.append(usernameText);
    new bootstrap.Tooltip(usernameText);

    country = $("#country");
    country.attr("title", userInfo.country);
    new bootstrap.Tooltip(country);
    country.prop("src", `/assets/country/${userInfo.country_alpha}`);

    $("#about").text(userInfo.about);

    // Game Archive
    const games = await (await apiRequest(`/profile/${username}/get_games`, {"limit": 10})).json();
    if (games.length) initilizePage(username, games)
    else {
        $(".no-games").show();
        $("#games").find("tbody").addClass("no-last-border-table");
    }
}
main();

async function initilizePage(username, games) {
    const tableBody = $("#games").find("tbody");
    $("#ratings").show();
    for (const game of games) {
        let gameElement = gameHTML.clone();
        gameElement.click(() => window.location.replace(`/game/${game.token}`))

        let whiteUsername = gameElement.find("#white-username");
        whiteUsername.text(game.white);
        if (game.white != "DELETED") whiteUsername.click(e => {
            e.stopPropagation();
            window.location.replace(`/user/${game.white}`);
        });

        let blackUsername = gameElement.find("#black-username");
        blackUsername.text(game.black);
        if (game.black != "DELETED") blackUsername.click(e => {
            e.stopPropagation();
            window.location.replace(`/user/${game.black}`);
        });

        let modeImage = gameElement.find("#mode-image");
        modeImage.prop("src", `../static/assets/modes/${game.game_settings.mode}.png`);
        modeImage.prop("title", game.game_settings.mode);
        new bootstrap.Tooltip(modeImage);

        gameElement.find("#white-wins").text(game.white_score);
        gameElement.find("#black-wins").text(game.black_score);

        let results = gameElement.find("#results");
        if (game.white_score == game.black_score && game.black_score == 0.5) {
            results.addClass("bi-plus-slash-minus");
            results.addClass("text-gray");
        } else if ((game.white_score == 1 && game.white == username) ||
            (game.black_score == 1 && game.black == username)) {
            results.addClass("bi-plus-square");
            results.addClass("text-success");
        } else {
            results.addClass("bi-dash-square");
            results.addClass("text-danger");
        }

        tableBody.append(gameElement);
    }

    // Rating Archive
    since = new Date();
    since.setMonth(since.getMonth() - 1);
    since = since / 1000 | 0;
    
    const ratings = await (await apiRequest(`/profile/${username}/get_ratings`, {"mode": "all", "since": since})).json();
    const ratingHolder = $("#ratings")

    for (const [mode, ratingData] of Object.entries(ratings)) {
        let rating = ratingData.archive.at(-1).elo;

        const ratingElement = ratingHTML.clone();

        ratingElement.find("#rating-image").attr("src", `../static/assets/modes/${mode}.png`)

        ratingElement.find("#elo").text(rating);
        ratingElement.find("#rating-mode").text(mode);

        ratingElement.find("#rating-highest").text(ratingData.max);
        ratingElement.find("#rating-lowest").text(ratingData.min);

        let ratingChangeElement = ratingElement.find("#rating-change")
        ratingChange = rating - ratingData.archive[0].elo;
        if (ratingChange > 0) {
            ratingChangeElement.text("+" + ratingChange)
            ratingChangeElement.css("color", "var(--soft-green)")
        }
        else if (ratingChange < 0) {
            ratingChangeElement.text(ratingChange)
            ratingChangeElement.css("color", "red")
        } else {
            ratingChangeElement.text("±" + ratingChange);
            ratingChangeElement.css("color", "gray");
        }

        ratingHolder.append(ratingElement);

        let data = ratingData.archive.map(rating => {
            return [new Date(rating.achieved_at).toLocaleString(), rating.elo];
        });
        data.push([new Date().toLocaleString(), rating]);
        google.charts.setOnLoadCallback(() => create_chart(ratingElement.find(".chart")[0], [["Date", "Elo"]].concat(data)));
    }
}

function create_chart(element, data) {
    data = google.visualization.arrayToDataTable(data);
    var options = {
        legend: "none",
        backgroundColor: "#1A1A1A",
        colors: ["#3ABA5A"],
        height: 50,
        vAxis: {
            textPosition: "none",
            gridlines: { color: "transparent" },
        },
        hAxis: {
            textPosition: "none",
            gridlines: { color: "transparent" }
        },
        chartArea: {
            width: "100%",
            height: "100%"
        },
        areaOpacity: 0.5,
        focusTarget: "category",
    };
    var chart = new google.visualization.AreaChart(element);
    chart.draw(data, options);

    $(window).on("resize", () =>  { chart.draw(data, options); });
    $(element).data("test", chart);
}

function collapseToggleButton() {
    button = $(this);
    if (button.hasClass("bi-caret-down-fill")) {
        button.removeClass("bi-caret-down-fill");
        button.addClass("bi-caret-up-fill");
    } else {
        button.addClass("bi-caret-down-fill");
        button.removeClass("bi-caret-up-fill");
    }
}