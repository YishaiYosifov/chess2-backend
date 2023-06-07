try {
    localStorage.setItem("test", "test");
    localStorage.removeItem("test");
} catch(e) {
    showAlert("It looks like cookies / localstorage is disabled. They are required for this site's functionality, enable them please :)");
}
loadAuthInfo().then(() => {
    console.log(authInfo);
    if (Object.keys(authInfo).length && authInfo["auth_method"] != "guest") {
        localStorage.removeItem("auth-info");
        window.location.replace("/login?a=session-expired");
    }
})

function changeBoardSize() {
    let board = $("#board")
    if (screen.width < 992) board.parent().hide()
    else {
        board.parent().show();
        board.height(board.width())
    }
}