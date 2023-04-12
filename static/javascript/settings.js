class Setting {
    constructor(requiresPassword = false, forAuth = "all") {
        this.requiresPassword = requiresPassword;
        this.forAuth = forAuth;
    }
}

var userInfo = {}

const settings = {
    "about": new Setting(),
    "username": new Setting(),
    "email": new Setting(requiresPassword=true, forAuth="website"),
    "password": new Setting(requiresPassword=false, forAuth="website")
}
var update = {"about": () => { return $("[input-for-setting='about']").val(); }}

async function main() {
    $("#save").prop("disabled", true);
    $(".disabled-input").prop("disabled", true);

    userInfo = await(await apiRequest("/profile/me/get_info")).json();

    for (const [setting, data] of Object.entries(settings)) {
        if (data.forAuth != "all" && data.forAuth != userInfo["authentication_method"]) {
            $(`#setting-${setting}`).remove();
            continue;
        }
        $(`[input-for-setting="${setting}"]`).val(userInfo[setting]);
    }

    const username = $("#username");
    username.text(userInfo["username"]);
    username.attr("title", userInfo["username"]);
    new bootstrap.Tooltip(username);

    $("#profile-picture").css("background", `url("/static/uploads/${userInfo["member_id"]}/profile-picture.jpeg"`);
}
main()

function censorEmail(email) {
    let [name, at] = email.split("@");
    let [secondary, top] = at.split(".");

    return `${partialCensor(name)}@${partialCensor(secondary)}.${top}`;
}
function partialCensor(text) { return text[0] + "*".repeat(text.length - 2) + text.slice(-1); }

function openFileSelector() { $("#profile-picture-upload").click(); }
async function selectProfilePicture() {
    response = await apiUpload("/profile/me/upload_profile_picture", "profile-picture", $("#profile-picture-upload").prop("files")[0]);
    if (response.status == 413) {
        showAlert("Profile Picture cannot be larger than 2MB!");
        return;
    } else if (!response.ok) {
        showAlert("Something went wrong.");
        return;
    }
    $("#profile-picture").css("background", `url("/static/uploads/${userInfo["member_id"]}/profile-picture.jpeg?${new Date().getTime()}"`);
    showAlert("Profile Picture Updated");
}

$("#change-username-button").click(function() {
    if ((userInfo["username_last_changed"] + 60 * 60 * 24 * 30) - Date.now() / 1000 > 0) {
        showAlert("Username changed too recently!");
        return;
    }

    enableSettingInput($(this));
})

function enableSettingInput(button) {
    if (!(button instanceof $)) { button = $(button); }
    button.hide(300, () => { button.remove(); })

    const setting = button.attr("enable-input-for-setting")

    let input = $(`[input-for-setting="${setting}"]`);
    input.prop("disabled", false);
    input.attr("style", "background-color: #FFFFFF !important");

    update[setting] = () => { return $(`[input-for-setting="${setting}"]`).val(); };
}

$(".settings-input").on("input", function () {
    let saveButton = $("#save");

    let toUpdate = removeNotChanged();
    if (!Object.keys(toUpdate).length) saveButton.prop("disabled", true);
    else saveButton.prop("disabled", false);
})

$("#save").click(async () => {
    let toUpdate = removeNotChanged();
    console.log(toUpdate)
    if (!Object.keys(toUpdate).length) return;

    let password = null;
    for (const setting of Object.keys(toUpdate)) {
        if (settings[setting].requiresPassword) {
            password = await confirmPassword();
            break;
        }
    }

    let data = {};
    Object.keys(toUpdate).forEach(key => { data[key] = toUpdate[key](); });
    let response = await apiRequest("/profile/me/update", Object.assign(data, {"password_confirmation": password}));
    if (response.status == 401) {
        showAlert("Wrong Password!");
        return;
    }
    else if (response.status == 500) {
        showAlert("Something went wrong.");
        return
    } else if (!response.ok) {
        showAlert(await response.text());
        return;
    }

    window.location.replace("/settings?a=settings_updated");
});

function removeNotChanged() {
    let toUpdate = Object.assign({}, update);
    for (const [key, value] of Object.entries(update)) {
        if (key in userInfo && userInfo[key] == value()) delete toUpdate[key];
    }
    return toUpdate;
}