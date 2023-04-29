class Setting {
    constructor(enabledByButton = false, requiresPassword = false, forAuth = "all") {
        this.enabledByButton = enabledByButton;

        this.requiresPassword = requiresPassword;
        this.forAuth = forAuth;
    }
}

var userInfo = {}

const settings = {
    "about": new Setting(enabledByButton=false, requiresPassword=false, forAuth="all"),
    "username": new Setting(enabledByButton=true),
    "email": new Setting(enabledByButton=true, requiresPassword=true, forAuth="website"),
    "country": new Setting(),
    "password": new Setting(enabledByButton=true, requiresPassword=false, forAuth="website")
}

async function main() {
    $("#save").prop("disabled", true);

    userInfo = await(await apiRequest("/profile/me/get_info")).json();
    $.getJSON(`${root}/static/countries.json`, async countries => {
        const dropdown = $("[input-for-setting='country']");
        for (const [alpha, country] of Object.entries(countries)) {
            let option = $(`<option value="${alpha}">${country}</option>`);
            if (alpha == userInfo["country_alpha"]) option.prop("selected", true)
            dropdown.append(option);
        }
    });

    for (const [setting, data] of Object.entries(settings)) {
        if (data.forAuth != "all" && data.forAuth != userInfo["auth_method"]) {
            $(`#setting-${setting}`).remove();
            continue;
        }

        let settingInput = $(`[input-for-setting="${setting}"]`)
        settingInput.val(userInfo[setting]);

        if (data.enabledByButton) settingInput.prop("disabled", true)
    }

    const username = $("#username");
    username.text(userInfo["username"]);
    username.attr("title", userInfo["username"]);
    new bootstrap.Tooltip(username);

    $("#profile-picture").css("background", `url("/static/uploads/${userInfo["member_id"]}/profile-picture.jpeg"`);
}
main()

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
    showAlert("Profile Picture Updated", "success");
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
}

$("[input-for-setting]").on("input", function () {
    let saveButton = $("#save");

    if (!Object.keys(getChangedSettings()).length) saveButton.prop("disabled", true);
    else saveButton.prop("disabled", false);
})

$("#save").click(async () => {
    let toUpdate = getChangedSettings();
    if (!Object.keys(toUpdate).length) return;

    let password = null;
    for (const setting of Object.keys(toUpdate)) {
        if (settings[setting].requiresPassword) {
            password = await confirmPassword();
            break;
        }
    }

    let response = await apiRequest("/profile/me/update", Object.assign(toUpdate, {"password_confirmation": password}));
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

    window.location.replace("/settings?a=settings-updated");
});

function getChangedSettings() {
    let toUpdate = {};
    for (const setting of Object.keys(settings)) {
        value = $(`[input-for-setting=${setting}]`).val();
        if (value != null && (!(setting in userInfo) || userInfo[setting] != value)) toUpdate[setting] = value;
    }
    return toUpdate;
}

$("#account-deletion-confirm").on("hidden.bs.modal", () => {
    $("#account-deletion-stage-1").show()
    $("#account-deletion-stage-2").hide();
});

$("#delete-account").click(async () => {
    $("#account-deletion-confirm").modal("hide");

    let username = $("#account-deletion-username").val();
    if (username != userInfo["username"]) {
        showAlert("Wrong Username!");
        return;
    }

    const response = await apiRequest("/auth/delete");
    if (response.status == 500) {
        showAlert("Something went wrong.");
        return;
    } else if (!response.ok) {
        showAlert(await response.text());
        return;
    }

    window.location.replace("/?a=account-deleted")
})