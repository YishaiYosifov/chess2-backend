var settings = {
    "mode": "Anarchy",
    "time_control": 3,
    "increment": 2
};

async function main() {
    if (await (await apiRequest("/game/has_outgoing")).json()) {
        $("#outgoing-game").show();
        $("*[setting] *").prop("disabled", true);
    }
    else $("#play").show();

    let savedSettings = getLocalStorage("game-settings");
    if (savedSettings) settings = savedSettings;
    $("#mode-preview").attr("src", `/static/assets/modes/thumbnails/${settings["mode"]}.webp`)

    for (const [setting, value] of Object.entries(settings)) {
        $(`[setting="${setting}"]`).find("button").filter(function() {
            return $(this).text().replace(/\s/g, "") == value;
        }).addClass("bg-secondary");
    }

    if (new URLSearchParams(location.search).get("s") == 1) $("#play").trigger("click");
    pathname = window.location.pathname.split("/").pop();
    pathname = (pathname == "") ? "/" : pathname;
    window.history.replaceState({}, null, pathname);
}

$(".setting-button").click(function() {
    const button = $(this);
    const parent = button.parent();

    parent.find(".setting-button").removeClass("bg-secondary");
    button.addClass("bg-secondary");

    let value = button.text().replace(/\s/g, "");
    if (isDigit(value)) value = parseInt(value);

    let setting = parent.attr("setting");
    settings[setting] = value;

    if (setting == "mode") $("#mode-preview").attr("src", `/static/assets/modes/thumbnails/${value}.webp`);
    
    localStorage.setItem("game-settings", JSON.stringify(settings));
});

$("#play").click(async function() {
    const response = await apiRequest("/game/pool/start", settings);
    if (!response.ok) {
        if (response.status == 409) showAlert(await response.text());
        else showAlert("Something went wrong.");
        return;
    } else if (response.status == 200) {
        window.location.replace(`/game/${await response.text()}`);
        return;
    }

    $(this).hide();
    $("*[setting] *").prop("disabled", true);

    $("#outgoing-game").show();
});

$("#cancel").click(() => {
    apiRequest("/game/cancel");
    
    $("#outgoing-game").hide();
    $("#play").show();
    $("*[setting] *").prop("disabled", false);
});

loadAuthInfo().then(main);