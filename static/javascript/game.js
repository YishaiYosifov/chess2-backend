const squareHTML = $($.parseHTML(`
    <div class="square">
        <img class="img-fluid" draggable="false">
    </div>
`));

const gameToken = window.location.pathname.split("/").pop();

var board;
var color;
var isLocalTurn;

async function main() {
    const boardContainer = $("#board");

    for (let row_index = 0; row_index < 10; row_index++) {
        for (let column_index = 0; column_index < 8; column_index++) {
            let square = squareHTML.clone();
            square.attr("id", `r${row_index}c${column_index}`);
            square.addClass(((row_index + column_index) % 2 == 0) ? "square-light" : "square-dark");

            boardContainer.append(square);
        }
    }

    const userID = authInfo["user_id"];

    const gameData = await (await apiRequest("/game/get_game", {"game_token": gameToken})).json();
    color = userID == gameData["white"] ? "white" : "black";
    board = gameData["board"];
    isLocalTurn = gameData["turn"] == userID;

    if (color == "white") board.reverse();
    refreshBoard();

    if (isLocalTurn) $(`img[color="${color}"]`).attr("draggable", true);
}
loadAuthInfo().then(main);

function refreshBoard() {
    for (const [row_index, row] of board.entries()) {
        for (const [column_index, column] of row.entries()) {
            let piece = $(`#r${row_index}c${column_index}`).find("img")
            if (!column) {
                piece.removeAttr("src");
                piece.removeAttr("color")
                continue;
            }
            
            piece.attr("src", `../static/assets/pieces/${column["name"]}-${column["color"]}.jpeg`);
            piece.attr("color", column["color"])
        }
    }
}

$(".square").on("dragover", e => { e.preventDefault(); });
$(".square").on("drop", function (e) {
    console.log(e, $(this));
});