function change_board_size() {
    let board = $("#board")
    if (screen.width < 992) board.parent().hide()
    else {
        board.parent().show();
        board.height(board.width())
    }
}