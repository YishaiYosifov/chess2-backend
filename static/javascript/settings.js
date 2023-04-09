var update = {"about": () => { return $("[settings-for='about']").val(); }}
var userInfo = {}

const requiresPassword = ["username", "email"]

async function main() {
    $("[settings-for='username']").prop("disabled", true);
    $("#save").prop("disabled", true)

    userInfo = await(await apiRequest("/profile/me/get_info")).json();

    for (const [attr, value] of Object.entries(userInfo)) $(`[settings-for="${attr}"]`).val(value);

    const username = $("#username")
    username.text(userInfo["username"])
    username.attr("title", userInfo["username"])
    new bootstrap.Tooltip(username)

    $(".email").text(censorEmail(userInfo["email"]))

    $("#profile-picture").css("background", `url("/static/uploads/${userInfo["member_id"]}/profile-picture.jpeg"`)
    
    console.log(userInfo);
}
main()

function censorEmail(email) {
    let [name, at] = email.split("@")
    let [secondary, top] = at.split(".")

    return `${partialCensor(name)}@${partialCensor(secondary)}.${top}`;
}
function partialCensor(text) { return text[0] + "*".repeat(text.length - 2) + text.slice(-1); }

function openFileSelector() { $("#profile-picture-upload").click(); }
async function selectProfilePicture() {
    response = await apiUpload("/profile/me/upload_profile_picture", "profile-picture", $("#profile-picture-upload").prop("files")[0]);
    if (response.status == 413) {
        showAlert("Profile Picture cannot be larger than 2MB!")
        return
    } else if (!response.ok) {
        showAlert("Something went wrong.")
        return
    }
    $("#profile-picture").css("background", `url("/static/uploads/${userInfo["member_id"]}/profile-picture.jpeg?${new Date().getTime()}"`);
    showAlert("Profile Picture Updated");
}

$("#change-username-button").click(function() {
    if ((userInfo["username_last_changed"] + 60 * 60 * 24 * 30) - Date.now() / 1000 > 0) {
        showAlert("Username changed too recently!")
        return;
    }

    enableSettingInput($(this))
})

function enableSettingInput(button) {
    if (!(button instanceof $)) { button = $(button); }
    button.hide(300, () => { button.remove(); })

    const setting = button.attr("enable-for")

    let input = $(`[settings-for="${setting}"]`);
    input.prop("disabled", false);
    input.attr("style", "background-color: #FFFFFF !important");

    update[setting] = () => { return $(`[settings-for="${setting}"]`).val(); };
}

$(".settings-input").on("input", function () {
    let saveButton = $("#save");

    let updateCheck = removeNotChanged();
    if (!Object.keys(updateCheck).length) saveButton.prop("disabled", true)
    else saveButton.prop("disabled", false)
})

$("#save").click(async () => {
    let updateCheck = removeNotChanged();
    if (!Object.keys(updateCheck).length) return;

    let password = null;
    for (const item of requiresPassword) {
        if (item in updateCheck) {
            password = await confirmPassword();
            break;
        }
    }

    let data = {}
    Object.keys(updateCheck).forEach(key => { data[key] = updateCheck[key](); });
    let response = await apiRequest("/profile/me/update", Object.assign(data, {"password_confirmation": password}));
    if (response.status == 401) {
        showAlert("Wrong Password!");
        return;
    } else if (!response.ok) {
        showAlert(await response.text());
        return;
    }

    window.location.replace("/settings?a=updated")
});

function removeNotChanged() {
    let updateCheck = Object.assign({}, update);
    for (const [key, value] of Object.entries(update)) {
        if (key in userInfo && userInfo[key] == value()) delete updateCheck[key];
    }
    return updateCheck;
}