try {
    localStorage.setItem("test", "test");
    localStorage.removeItem("test");

    localStorage.removeItem("auth-info");
} catch(e) {
    showAlert("It looks like cookies / localstorage is disabled. They are required for this site's functionality, enable them please :)");
}

function changeBoardSize() {
    let board = $("#board")
    if (screen.width < 992) board.parent().hide()
    else {
        board.parent().show();
        board.height(board.width())
    }
}