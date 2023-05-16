const squareHTML = $($.parseHTML(`
    <div class="square">
        <img class="img-fluid valid-move" src="../static/assets/valid-move.png" draggable="false">
    </div>
`));
const pieceHTML = $($.parseHTML(`<img class="img-fluid piece" draggable="false">`))

const gameToken = window.location.pathname.split("/").pop();

var board;
var color;
var isLocalTurn;

var movingElement;

var boardHeight;
var boardWidth;

async function main() {
    const boardContainer = $("#board");
    const userID = authInfo["user_id"];

    const gameData = await (await apiRequest("/game/get_game", {"game_token": gameToken})).json();
    color = userID == gameData["white"] ? "white" : "black";
    board = gameData["board"];

    board = board.map(
        (row, rowIndex) => row.map(
            (column, columnIndex) => ({"x": columnIndex, "y": rowIndex, "piece": column})
        )
    );
    boardHeight = board.length;
    boardWidth = board[0].length;
    
    isLocalTurn = gameData["turn"] == userID;

    let tempBoard = structuredClone(board);
    const colorMod = color == "white" ? 1 : 0
    if (color == "white") tempBoard.reverse()
    for (const [rowIndex, row] of tempBoard.entries()) {
        for (const [columnIndex, column] of row.entries()) {
            let fixedRowIndex = rowIndex;
            if (color == "white") fixedRowIndex = board.length - fixedRowIndex - 1;

            const square = squareHTML.clone();
            square.attr("id", `${fixedRowIndex}-${columnIndex}`);
            square.addClass(((rowIndex + columnIndex) % 2 == colorMod) ? "square-light" : "square-dark");

            if (column["piece"]) {
                const piece = pieceHTML.clone();
                piece.attr("src", `../static/assets/pieces/${column["piece"]["name"]}-${column["piece"]["color"]}.png`);
                piece.attr("color", column["piece"]["color"]);
                piece.appendTo(square)
            }

            boardContainer.append(square);
        }
    }

    if (isLocalTurn) enableDraggable();

    $(`[color=${color}]`).on("mousedown", function() {
        if (!isLocalTurn) return;

        $(".valid-move").hide().parent().droppable().droppable("disable");
    
        movingElement = $(this)
        var [y, x] = movingElement.parent().attr("id").split("-");
        x = parseInt(x);
        y = parseInt(y);
    
        for (const validMove of allLegal[board[y][x]["piece"]["name"]](x, y)) {
            const moveIndicator = $(`#${validMove["y"]}-${validMove["x"]}`).find(".valid-move");
            moveIndicator.fadeIn(300);
            
            moveIndicator.parent().droppable({drop: (event, ui) => move($(ui.helper), $(event.target))}).droppable("enable");
        }
    })

    $(".square").click(function() {
        if ($(this).find(".valid-move").is(":hidden")) return;
        move(movingElement, $(this))
    })
}
loadAuthInfo().then(main);

async function move(originElement, destinationElement) {
    const originID = originElement.parent().attr("id");
    const destinationID = destinationElement.attr("id");

    if (originID == destinationID) return;

    const [originY, originX] = originID.split("-");
    const [destinationY, destinationX] = destinationID.split("-");
    
    await movePiece(originElement, destinationElement, originX, originY, destinationX, destinationY);

    $(".valid-move").hide();
    disableDraggable();

    gameNamespace.emit("move", {"origin_x": originX, "origin_y": originY, "destination_x": destinationX, "destination_y": destinationY});
}

function enableDraggable() {
    isLocalTurn = true;
    $(`img[color="${color}"]`).draggable({
        containment: $("#board"),
        cursor: "grabbing",
        stop: (event) =>  $(event.target).css("top", "").css("left", ""),
        zIndex: 1
    }).draggable("enable");
}

function disableDraggable() {
    isLocalTurn = false;
    $(`img[color="${color}"]`).draggable().draggable("disable");
}

async function movePiece(originElement, destinationElement, originX, originY, destinationX, destinationY) {
    let tempBoardPiece = board[originY][originX];
    board[originY][originX] = {"x": tempBoardPiece["x"], "y": tempBoardPiece["y"]};
    delete tempBoardPiece["x"];
    delete tempBoardPiece["y"];

    tempBoardPiece["moved"]++;
    Object.assign(board[destinationY][destinationX], tempBoardPiece);

    const tempPiece = originElement.clone();
    tempPiece
        .css("position", "absolute")
        .css("left", originElement.offset().left)
        .css("top", originElement.offset().top)
        .css("width", originElement.width())
        .css("height", originElement.height())
        .css("z-index", 1);
    originElement.detach();

    tempPiece.appendTo("body");
    await tempPiece.animate({
        left: destinationElement.offset().left,
        top: destinationElement.offset().top
    }, 100).promise();

    destinationElement.find(".piece").remove();

    tempPiece.remove();
    originElement.appendTo(destinationElement);
}

gameNamespace.on("move", (data) => {
    const originElement = $(`#${data["origin"]["y"]}-${data["origin"]["x"]}`).find(".piece");
    const destinationElement = $(`#${data["destination"]["y"]}-${data["destination"]["x"]}`);
    movePiece(originElement, destinationElement, data["origin"]["x"], data["origin"]["y"], data["destination"]["x"], data["destination"]["y"])

    enableDraggable();
});


function pieceSlice(pieces, capture = true) {
    const fromPiece = pieces[0]["piece"];

    pieces.shift();
    for (const [index, square] of pieces.entries()) {
        if (square["piece"]) return pieces.slice(0, fromPiece["color"] != square["piece"]["color"] && capture ? index + 1: index);
    }
    return pieces;
}
function diagonal(arr) {
    let diagonal = []
    for (const [index, _] of arr.entries()) {
        let diagonalElement = arr[index][index];
        if (!diagonalElement) break;
        diagonal.push(diagonalElement);
    }

    return diagonal;
}

const straightMoves = (x, y) =>
        pieceSlice(board[y].slice(0, x + 1).reverse()).concat(
            pieceSlice(board[y].slice(x, boardWidth)),

            pieceSlice(board.slice(0, y + 1).map(column => column[x]).reverse()),
            pieceSlice(board.slice(y, boardHeight).map(column => column[x]))
        );
const diagonalMoves = (x, y) =>
    pieceSlice(diagonal(
        board.slice(y, boardHeight).map(column => column.slice(x, boardWidth))
    )).concat(
        pieceSlice(diagonal(
            board.slice(0, y + 1).map(column => column.slice(0, x + 1).reverse()).reverse()
        )),

        pieceSlice(diagonal(
            board.slice(0, y + 1).map(column => column.slice(x, boardWidth)).reverse()
        )),
        pieceSlice(diagonal(
            board.slice(y, boardHeight).map(column => column.slice(0, x + 1).reverse())
        ))
  );

const pawnMoves = (x, y, amount) => {
    const piece = board[y][x];

    if (piece["piece"]["color"] == "white") return pieceSlice(board.slice(y, y + amount + 1).map(column => column[x]), false);
    else return pieceSlice(board.slice(y - amount, y + 1).map(column => column[x]).reverse(), false);
}
const horseMoves = (x, y) => {
    const piece = board[y][x]["piece"];

    let moves = [];
    for (let i of [-2, -1, 1, 2]) {
        for (let j of [-2, -1, 1, 2]) {
            if (Math.abs(i) == Math.abs(j)) continue;

            const checkX = x - i;
            const checkY = y - j;
            if (checkX < 0 || checkX > boardWidth - 1|| checkY < 0 || checkY > boardHeight - 1) continue;

            const checkSquare = board[checkY][checkX]
            if (checkSquare["piece"] && checkSquare["piece"]["color"] == piece["color"]) continue;
            moves.push(checkSquare);
        }
    }
    return moves;
}

const allLegal = {
    "rook": straightMoves,
    "bishop": diagonalMoves,
    "horse": horseMoves,
    "king": (x, y) => {
        const piece = board[y][x]["piece"];

        let moves = [];
        for (let i of [-1, 0, 1]) {
            for (let j of [-1, 0, 1]) {
                if (i == 0 && j == 0) continue;

                let checkX = x - i;
                let checkY = y - j;
                if (checkX < 0 || checkX > 7 || checkY < 0 || checkY > 9) continue;

                const square = board[checkY][checkX];
                if (square["piece"] && square["piece"]["color"] == piece["color"]) continue;
                moves.push(square);
            }
        }
        return moves;
    },
    "queen": (x, y) => diagonalMoves(x, y).concat(straightMoves(x, y)),
    "child-pawn": (x, y) => pawnMoves(x, y, board[y][x]["piece"]["moved"] == 0 ? 2 : 1),
    "pawn": (x, y) => {
        let limit = 1;
        if (board[y][x]["piece"]["moved"] == 0) {
            limit = 2;
            if ((boardWidth % 2 == 0 && (x == (boardWidth / 2) - 1 || x == boardWidth / 2)) || (board % 2 != 0 && x == Math.floor(boardWidth / 2))) limit = 3;
        }
        return pawnMoves(x, y, limit);
    },
    "archbishop": (x, y) => straightMoves(x, y).filter(move => {
        if (x == move["x"]) return Math.abs(y - move["y"]) % 2 == 0;
        else return Math.abs(x - move["x"]) % 2 == 0;
    }),
    "xook": diagonalMoves,
    "antiqueen": horseMoves,
    "knook": (x, y) => straightMoves(x, y).filter(move => move["piece"]).concat(horseMoves(x, y).filter(move => !move["piece"]))
};