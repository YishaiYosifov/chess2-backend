const squareHTML = $($.parseHTML(`
    <div class="square">
        <img class="img-fluid valid-move" src="../static/assets/valid-move.png" draggable="false">
    </div>
`));
const pieceHTML = $($.parseHTML(`<img class="img-fluid piece" draggable="false">`))

const gameToken = window.location.pathname.split("/").pop();

var moves;
var board;
var color;
var isLocalTurn;

var movingElement;

var boardHeight;
var boardWidth;

var allLegalCache = {};

async function main() {
    const boardContainer = $("#board");
    const userID = authInfo.user_id;

    const gameData = await (await apiRequest("/game/get_game", {"game_token": gameToken})).json();
    color = userID == gameData.white ? "white" : "black";
    board = gameData.board;
    moves = gameData.moves;

    boardHeight = board.length;
    boardWidth = board[0].length;
    
    isLocalTurn = gameData.turn == userID;

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

            if (column.piece) {
                const piece = pieceHTML.clone();
                piece.attr("src", `../static/assets/pieces/${column.piece.name}-${column.piece.color}.png`);
                piece.attr("color", column.piece.color);
                piece.appendTo(square)
            }

            boardContainer.append(square);
        }
    }

    if (isLocalTurn) enableDraggable();

    $(`[color=${color}]`).on("mousedown", function() {
        if (!isLocalTurn) return;

        $(".valid-move").hide().parent().droppable().droppable("disable");
    
        movingElement = $(this);
        const id = movingElement.parent().attr("id");
        var [y, x] = id.split("-");
        x = parseInt(x);
        y = parseInt(y);
    
        let legalMoves = allLegalCache[id] ?? allLegal[board[y][x].piece.name](x, y);
        allLegalCache[id] = legalMoves;
        for (const validMove of legalMoves) {
            const moveIndicator = $(`#${validMove.y}-${validMove.x}`).find(".valid-move");
            moveIndicator.fadeIn(300);
            
            moveIndicator.parent().droppable({drop: (event, ui) => move($(ui.helper), $(event.target))}).droppable("enable");
        }
    })

    $(".square").click(function() {
        if ($(this).find(".valid-move").is(":hidden")) return;
        move(movingElement, $(this));
    });

    const arrowsCanvas = document.querySelector("#arrows-canvas");
    arrowsCanvas.width = boardContainer.width();
    arrowsCanvas.height = boardContainer.height();
}
loadAuthInfo().then(main);

async function move(originElement, destinationElement) {
    $(".valid-move").hide();
    movingElement = null;
    
    const originID = originElement.parent().attr("id");
    const destinationID = destinationElement.attr("id");

    if (originID == destinationID) return;

    let [originY, originX] = originID.split("-");
    let [destinationY, destinationX] = destinationID.split("-");
    originX = parseInt(originX);
    originY = parseInt(originY);
    destinationX = parseInt(destinationX);
    destinationY = parseInt(destinationY);
    
    let maxForced = {"priority": 0};
    let maxPlayedPriority = 0;
    for (const row of board) {
        for (const square of row) {
            if (!square.piece || square.piece.color != color || !(square.piece.name in forcedMoves)) continue;

            const priority = forcedMoves[square.piece.name].priority;
            const [results, foundForcedMoves] = forcedMoves[square.piece.name].checker(square, destinationX, destinationY);
            if (!results) continue;
            else if (results == 2 && priority > maxPlayedPriority) maxPlayedPriority = priority;

            if (priority > maxForced.priority) maxForced = {"priority": priority, "toSquare": foundForcedMoves};
            else if (priority == maxForced.priority) maxForced["toSquare"] = maxForced["toSquare"].concat(foundForcedMoves);
        }
    }
    if (maxForced.priority > maxPlayedPriority) {
        for (let i = 0; i < 2; i++) {
            if (movingElement) return;

            for (const [fromSquare, toSquare] of maxForced["toSquare"]) {
                const fromElement = $(`#${fromSquare.y}-${fromSquare.x}`);
                const toElement = $(`#${toSquare.y}-${toSquare.x}`);
                fromElement.css("background-color", "#C27356");
                toElement.css("background-color", "#C27356");
                drawArrow(fromElement, toElement);
            }
            await sleep(250);
            clearArrows();
            $(".square").css("background-color", "");
            await sleep(250);
        }
        return;
    }

    await movePiece(originElement, destinationElement, originX, originY, destinationX, destinationY);
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
    $(".valid-move").hide();
    $(`img[color="${color}"]`).draggable().draggable("disable");
}

async function movePiece(originElement, destinationElement, originX, originY, destinationX, destinationY) {
    allLegalCache = {};
    moves.push({"piece": board[originY][originX].piece.name, "origin": {"x": originX, "y": originY}, "destination": {"x": destinationX, "y": destinationY}});

    let tempBoardPiece = structuredClone(board[originY][originX]);
    if (tempBoardPiece.piece.name == "pawn" && Math.abs(originX - destinationX) > 1) {
        const yOffset = tempBoardPiece.piece.color == "white" ? -1 : 1;
        const enpassantDiagonal = diagonal(originX, originY + yOffset, destinationX, destinationY + yOffset);
        for (const [index, square] of Object.entries(enpassantDiagonal)) {
            square.piece = null;
            $(`#${square.y}-${square.x}`).find(".piece").delay(index * 30).fadeOut(100, function() { $(this).remove(); });
        }
    }
    board[originY][originX].piece = null;

    delete tempBoardPiece.x;
    delete tempBoardPiece.y;
    tempBoardPiece.piece.moved = true;

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
    const originElement = $(`#${data.origin.y}-${data.origin.x}`).find(".piece");
    const destinationElement = $(`#${data.destination.y}-${data.destination.x}`);
    movePiece(originElement, destinationElement, data.origin.x, data.origin.y, data.destination.x, data.destination.y);

    if (data.turn == color) enableDraggable();
    else disableDraggable();
});
gameNamespace.on("exception", (data) => {
    showAlert("Something went wrong. Please refresh the page");
    console.error(data);
})


function pieceSlice(pieces, capture = true) {
    const fromPiece = pieces[0].piece;

    pieces.shift();
    for (const [index, square] of pieces.entries()) {
        if (square.piece) return pieces.slice(0, fromPiece.color != square.piece.color && capture ? index + 1: index);
    }
    return pieces;
}
function diagonal(x1, y1, x2, y2) {
    let sliced = board.slice(Math.min(y1, y2), Math.max(y1, y2) + 1).map(column => {
        let columnSlice = column.slice(Math.min(x1, x2), Math.max(x1, x2) + 1);
        if (x1 > x2) columnSlice.reverse();
        return columnSlice;
    });

    if (y1 > y2) sliced.reverse();

    let diagonal = [];
    for (const [index, _] of sliced.entries()) {
        let diagonalElement = sliced[index][index];
        if (!diagonalElement) break;
        diagonal.push(diagonalElement);
    }
    if (diagonal.at(-1) == board[y1][x1]) diagonal.reverse();

    return diagonal;
}

const straightMoves = (x, y) =>
        pieceSlice(board[y].slice(0, x + 1).reverse()).concat(
            pieceSlice(board[y].slice(x, boardWidth)),

            pieceSlice(board.slice(0, y + 1).map(column => column[x]).reverse()),
            pieceSlice(board.slice(y, boardHeight).map(column => column[x]))
        );
const diagonalMoves = (x, y) =>
    pieceSlice(diagonal(x, y, boardWidth, boardHeight)).concat(
        pieceSlice(diagonal(x, y, 0, boardHeight)),
        pieceSlice(diagonal(x, y, 0, 0)),
        pieceSlice(diagonal(x, y, boardWidth, 0))
    );

const pawnMoves = (x, y, amount) => {
    let pawnMoves = [];
    let yOffset;
    if (color == "white") {
        pawnMoves = pieceSlice(board.slice(y, y + amount + 1).map(column => column[x]), false);
        yOffset = boardHeight;
    }
    else {
        pawnMoves = pieceSlice(board.slice(y - amount, y + 1).map(column => column[x]).reverse(), false);
        yOffset = 0;
    }
    
    if (!moves) return pawnMoves;
    for (const xOffset of [0, boardWidth]) {
        let diagonalSlice = diagonal(x, y, xOffset, yOffset)
        diagonalSlice.shift();
        for (const [index, square] of Object.entries(diagonalSlice)) {
            if (!square.piece) {
                const enpassantSquare = board[square.y + (color == "white" ? -1 : 1)][square.x];

                const lastMove = moves.at(-1);
                if (!enpassantSquare.piece ||
                    !enpassantSquare.piece.name.includes("pawn") ||
                    enpassantSquare.piece.color == color ||
                    (index == 0 &&
                        (!isDictEqual(lastMove.destination, {"x": enpassantSquare.x, "y": enpassantSquare.y}) ||
                        Math.abs(lastMove.origin.y - lastMove.destination.y) < 2)
                    )) break;
                pawnMoves.push(square);
            } else {
                if (index == 0 && square.piece.color != color) pawnMoves.push(square);
                break;
            }
        }
    }
    return pawnMoves;
}
const horseMoves = (x, y) => {
    const piece = board[y][x].piece;

    let moves = [];
    for (let i of [-2, -1, 1, 2]) {
        for (let j of [-2, -1, 1, 2]) {
            if (Math.abs(i) == Math.abs(j)) continue;

            const checkX = x - i;
            const checkY = y - j;
            if (checkX < 0 || checkX > boardWidth - 1|| checkY < 0 || checkY > boardHeight - 1) continue;

            const checkSquare = board[checkY][checkX]
            if (checkSquare.piece && checkSquare.piece.color == piece.color) continue;
            moves.push(checkSquare);
        }
    }
    return moves;
}

function isValidEnPassant(square, side) {
    const yOffset = color == "white" ? -1 : 1;
    const capturePiece = board[square.y + yOffset][square.x + side];
    if (!moves || !capturePiece || !square.piece || !square.piece.name.includes("pawn")) return false;

    const lastMove = moves.at(-1);
    const target = board[square.y][square.x + side];

    return !capturePiece.piece &&
            target &&
            target.piece &&
            target.piece.name.includes("pawn") &&
            Math.abs(lastMove.origin.y - lastMove.destination.y) > 1;
}

const allLegal = {
    "rook": straightMoves,
    "bishop": diagonalMoves,
    "horse": horseMoves,
    "king": (x, y) => {
        const piece = board[y][x].piece;

        let moves = [];
        for (let i of [-1, 0, 1]) {
            for (let j of [-1, 0, 1]) {
                if (i == 0 && j == 0) continue;

                let checkX = x - i;
                let checkY = y - j;
                if (checkX < 0 || checkX > 7 || checkY < 0 || checkY > 9) continue;

                const square = board[checkY][checkX];
                if (square.piece && square.piece.color == piece.color) continue;
                moves.push(square);
            }
        }
        return moves;
    },
    "queen": (x, y) => diagonalMoves(x, y).concat(straightMoves(x, y)),
    "child-pawn": (x, y) => pawnMoves(x, y, !board[y][x].piece.moved ? 2 : 1),
    "pawn": (x, y) => {
        let limit = 1;
        if (!board[y][x].piece.moved) {
            limit = 2;
            if ((boardWidth % 2 == 0 && (x == (boardWidth / 2) - 1 || x == boardWidth / 2)) || (board % 2 != 0 && x == Math.floor(boardWidth / 2))) limit = 3;
        }
        return pawnMoves(x, y, limit);
    },
    "archbishop": (x, y) => straightMoves(x, y).filter(move => {
        if (x == move.x) return Math.abs(y - move.y) % 2 == 0;
        else return Math.abs(x - move.x) % 2 == 0;
    }),
    "xook": diagonalMoves,
    "antiqueen": horseMoves,
    "knook": (x, y) => straightMoves(x, y).filter(move => move.piece).concat(horseMoves(x, y).filter(move => !move.piece))
};

// Forced Moves
// @returns
// 0: not forced
// 1: forced, not played
// 2: played
function forcedEnPassantMoves(square, destinationX, destinationY) {
    if (!moves) return [0, null];

    let yOffset = color == "white" ? 1 : -1;
    let enpassantMoves = [];
    for (const xOffset of [-1, 1]) {
        if (!isValidEnPassant(square, xOffset)) continue;
        enpassantMoves.push([square, board[square.y + yOffset][square.x + xOffset]]);

        const m = ((square.y + yOffset) - square.y) / ((square.x + xOffset) - square.x);
        const b = square.y - m * square.x;
        const expectedY = m * destinationX + b;
        if (expectedY == destinationY) return [2, null];
    }

    if (enpassantMoves.length) return [1, enpassantMoves]
    return [0, null];
}
const forcedMoves = {
    "pawn": {
        "priority": Infinity,
        "checker": forcedEnPassantMoves
    },
    "child-pawn": {
        "priority": Infinity,
        "checker": forcedEnPassantMoves
    }
};

// Arrow
arrows = [];
function drawArrow(fromElement, toElement) {
    const boardOffset = $("#board").offset();
    let [y1, x1] = Object.values(fromElement.offset());
    let [y2, x2] = Object.values(toElement.offset());

    const squareOffset = $(".square").width() / 2;
    y1 -= boardOffset.top;
    y1 += squareOffset

    x1 -= boardOffset.left;
    x1 += squareOffset;

    y2 -= boardOffset.top;
    y2 += squareOffset;

    x2 -= boardOffset.left;
    x2 += squareOffset;

    const viewportMin = Math.min($(window).width(), $(window).height());

    const context = document.querySelector("#arrows-canvas").getContext("2d");
    context.beginPath();
    context.lineWidth = percent(1.5, viewportMin);
    context.strokeStyle = "orange";
    context.fillStyle = "orange";
    context.lineCap = "round"
    
    let radians = Math.atan((y2 - y1) / (x2 - x1));
    if (x1 == x2) radians += 90 * Math.PI / 180
    else radians += ((x2 > x1) ? 90 : -90) * Math.PI / 180;
    
    context.moveTo(x1, y1);
    context.lineTo(x2, y2);
    context.stroke();

    context.save();
    context.beginPath();

    context.translate(x2, y2);
    context.rotate(radians);
    context.moveTo(0, 0);

    context.lineTo(percent(3, viewportMin), percent(5, viewportMin));
    context.lineTo(-percent(3, viewportMin), percent(5, viewportMin));

    context.closePath();
    context.restore();
    context.fill();

    arrows.push({"from": fromElement, "to": toElement})
}

function clearArrows() {
    arrows = [];

    const arrowsCanvas = document.querySelector("#arrows-canvas");
    const context = arrowsCanvas.getContext("2d");
    context.clearRect(0, 0, arrowsCanvas.width, arrowsCanvas.height);
}

var resizeTimeout;
$(window).on("resize", () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        const boardContainer = $("#board");
        const arrowsCanvas = document.querySelector("#arrows-canvas");
        arrowsCanvas.width = boardContainer.width();
        arrowsCanvas.height = boardContainer.height();
        for (const [index, arrowData] of Object.entries(arrows)) {
            arrows.splice(index, 1);
            drawArrow(arrowData.from, arrowData.to);
        }
    }, 30);
});