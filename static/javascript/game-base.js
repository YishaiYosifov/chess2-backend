const squareHTML = $($.parseHTML(`
    <div class="square">
        <img class="img-fluid valid-move" src="../static/assets/valid-move.png" draggable="false">
    </div>
`));
const pieceHTML = $($.parseHTML(`<img class="img-fluid piece" draggable="false">`))

const gameToken = window.location.pathname.split("/").pop();
const CSSProperties = getComputedStyle(document.documentElement, null);

var moves;
var board;
var color;
var isLocalTurn;

var highlightElement;
var movingElement;

var boardHeight;
var boardWidth;

var allLegalCache = {};
var game;

async function baseConstructBoard() {
    const boardContainer = $("#board");
    const userID = authInfo.user_id;

    const gameData = await (await apiRequest("/game/get_game", {"game_token": gameToken})).json();
    color = userID == gameData.white ? "white" : "black";
    board = gameData.board;
    moves = gameData.moves;

    boardHeight = board.length;
    boardWidth = board[0].length;
    
    isLocalTurn = gameData.turn == userID;

    const promotionCard = $("#promotion-card");
    for (const piece of Object.keys(allLegal)) {
        if (piece.includes("pawn") || piece == "king") continue;

        const image = $("<img></img>");
        image.addClass("img-fluid");
        image.addClass("promotion-piece");

        image.attr("id", `promotion-${piece}`);

        image.attr("draggable", "false");
        image.attr("src", `../static/assets/pieces/${piece}-${color}.png`);
        image.appendTo(promotionCard);
    }

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
}

class GameBase {
    constructor() {
        game = this;
        if (isLocalTurn) enableDraggable();

        gameNamespace.on("move", this.socketioMove);
        gameNamespace.on("exception", this.socketioException);

        $(`[color=${color}]`).mousedown(function(event) {
            if (event.which != 1 || !isLocalTurn) return;
    
            $(".valid-move").hide().parent().droppable().droppable("disable");
        
            movingElement = $(this);
            const id = movingElement.parent().attr("id");
            let [y, x] = id.split("-");
            x = parseInt(x);
            y = parseInt(y);
        
            let legalMoves = allLegalCache[id] ?? allLegal[board[y][x].piece.name](x, y);
            allLegalCache[id] = legalMoves;
            for (const validMove of legalMoves) {
                const moveIndicator = $(`#${validMove.y}-${validMove.x}`).find(".valid-move");
                moveIndicator.fadeIn(300);
                
                moveIndicator.parent().droppable({drop: (event, ui) => game.moveListener($(ui.helper), $(event.target))}).droppable("enable");
            }
        });
    
        $(".square").mousedown(function(event) {
            if (event.which == 1) {
                clearAllHighlights();
                clearAllArrows();
            }
            else highlightElement = $(this);
        });
        $(".square").mouseup(function(event) {
            if (event.which == 1) return;
    
            const currentSquare = $(this);
            if (currentSquare.is(highlightElement)) {
                if (currentSquare.hasClass("highlight")) clearHighlight(currentSquare)
                else highlightSquare(currentSquare);
            } else {
                const highlightElementID = highlightElement.attr("id");
                const currentSquareID = currentSquare.attr("id");
                if (highlightElementID in arrows && currentSquareID in arrows[highlightElementID]) clearArrow(highlightElement, currentSquare);
                else drawArrow(highlightElement, currentSquare);
            }
        });
    
        $(".square").click(function() {
            if ($(this).find(".valid-move").is(":hidden")) return;
            game.moveListener(movingElement, $(this));
        });
    }

    async moveListener(originElementImage, destinationElement) {
        $(".valid-move").hide();
        
        const originID = originElementImage.parent().attr("id");
        const destinationID = destinationElement.attr("id");
    
        if (originID == destinationID) return;
    
        let [originY, originX] = originID.split("-");
        let [destinationY, destinationX] = destinationID.split("-");
        originX = parseInt(originX);
        originY = parseInt(originY);
        destinationX = parseInt(destinationX);
        destinationY = parseInt(destinationY);
    
        disableDraggable();
    
        let move_data = {};
        const originSquare = board[originY][originX]
        if (originSquare.piece.name.includes("pawn") && (destinationY == board.length - 1 || destinationY == 0)) {
            const promotionCard = $("#promotion-card");
            promotionCard.appendTo(destinationElement)
            promotionCard.fadeIn(300);
    
            const rejectFunction = function() {
                if ($(this).is(destinationElement)) return;
                $(".square").off("click", rejectFunction);

                enableDraggable();
                revertPiece(originElementImage);
                promotionCard.fadeOut(300);
                reject("Promotion Canceled");
            }
    
            const promotionPiece = await new Promise((resolve, reject) => {
                $(".promotion-piece").click(function() {
                    promotionCard.fadeOut(300);
                    $(".square").off("click", rejectFunction);
                    resolve($(this).attr("id").split("-").at(-1));
                });
                $(".square").click(rejectFunction);
            });
            $(".promotion-piece").off("click");
            move_data["promote_to"] = promotionPiece;
        } else if (originSquare.piece.name == "king" && originY == destinationY && Math.abs(originX - destinationX) > 1) {
            if (originX > destinationX) destinationX = 2;
            else destinationX = 5;
        }
        Object.assign(move_data, {"origin_x": originX, "origin_y": originY, "destination_x": destinationX, "destination_y": destinationY});
    
        gameNamespace.emit("move", move_data);
    }

    async movePiece(originElementImage, destinationElement, originX, originY, destinationX, destinationY, promoteTo) {
        movingElement = null;
        allLegalCache = {};
        moves.push({"piece": board[originY][originX].piece.name, "origin": {"x": originX, "y": originY}, "destination": {"x": destinationX, "y": destinationY}});
    
        let boardSquare = structuredClone(board[originY][originX]);
        if (boardSquare.piece.name.includes("pawn") && Math.abs(originX - destinationX) >= 2) {
            const yOffset = boardSquare.piece.color == "white" ? -1 : 1;
            const enpassantDiagonal = diagonal(originX, originY + yOffset, destinationX, destinationY + yOffset);
            for (const [index, square] of Object.entries(enpassantDiagonal)) {
                square.piece = null;
                $(`#${square.y}-${square.x}`).find(".piece").delay(index * 30).fadeOut(100, function() { $(this).remove(); });
            }
        } else if (boardSquare.piece.name == "king" && Math.abs(originX - destinationX) > 1) {
            let castleRookCopy;
            let rookCastleDestination;
            if (originX > destinationX) {
                castleRookCopy = structuredClone(board[originY][0]);
                rookCastleDestination = $(`#${originY}-2`);

                board[originY][0].piece = null;
                board[originY][2].piece = castleRookCopy.piece;
            } else {
                castleRookCopy = structuredClone(board[originY].at(-1));
                rookCastleDestination = $(`#${originY}-4`);

                board[originY].at(-1).piece = null;
                board[originY][4].piece = castleRookCopy.piece;
            }
            animateMovement($(`#${castleRookCopy.y}-${castleRookCopy.x}`).find(".piece"), rookCastleDestination);
        }
        board[originY][originX].piece = null;
    
        delete boardSquare.x;
        delete boardSquare.y;
        boardSquare.piece.moved = true;
    
        Object.assign(board[destinationY][destinationX], boardSquare);

        await animateMovement(originElementImage, destinationElement);
        const destinationPiece = board[destinationY][destinationX].piece;
        if (destinationPiece.name.includes("pawn") && (destinationY == 0 || destinationY == boardHeight - 1)) {
            originElementImage.attr("src", `../static/assets/pieces/${promoteTo}-${destinationPiece.color}.png`);
            destinationPiece.name = promoteTo;
        }
    }

    async socketioMove(data) {
        const originElement = $(`#${data.origin.y}-${data.origin.x}`).find(".piece");
        const destinationElement = $(`#${data.destination.y}-${data.destination.x}`);
        await game.movePiece(originElement, destinationElement, data.origin.x, data.origin.y, data.destination.x, data.destination.y, data["promote_to"]);
    
        if (data.turn == color) enableDraggable();
        else disableDraggable();
    }

    async socketioException(data) {
        console.error(data);
        if (movingElement) {
            revertPiece(movingElement);
            movingElement = null;
        }
    
        if (data["code"] == 5) {
            enableDraggable();
    
            const forcedMoves = data["message"];
            for (let i = 0; i < 2; i++) {
                if (movingElement) return;
    
                for (const [fromSquare, toSquare] of forcedMoves) {
                    const fromElement = $(`#${fromSquare.y}-${fromSquare.x}`);
                    const toElement = $(`#${toSquare.y}-${toSquare.x}`);
                    highlightSquare(fromElement);
                    highlightSquare(toElement);
                    drawArrow(fromElement, toElement);
                }
                await sleep(300);
                clearAllArrows();
                clearAllHighlights();
                await sleep(300);
            }
        } else showAlert("Something went wrong. Please refresh the page");
    }
}

function enableDraggable() {
    isLocalTurn = true;
    $(`img[color="${color}"]`).draggable({
        containment: $("#board"),
        cursor: "grabbing",
        revert: "invalid",
        revertDuration: 100,
        zIndex: 1
    }).draggable("enable");
}

function disableDraggable() {
    isLocalTurn = false;
    $(".valid-move").hide();
    $(`img[color="${color}"]`).draggable().draggable("disable");
}

function revertPiece(pieceImage) {
    pieceImage.animate({
        "top": "0px",
        "left": "0px"
    }, 100);
}

function highlightSquare(square) {
    square.addClass("highlight");
    square.animate({
        "background-color": square.hasClass("square-dark") ?
            CSSProperties.getPropertyValue("--highlight-dark") : CSSProperties.getPropertyValue("--highlight-light")
        }, 200);
}
async function clearHighlight(square) {
    await square.animate({
        "background-color": square.hasClass("square-dark") ?
            CSSProperties.getPropertyValue("--square-dark") : CSSProperties.getPropertyValue("--square-light")
        }, 200).promise();
    square.removeClass("highlight");
    square.css("background-color", "");
}
function clearAllHighlights() {
    $(".highlight").each((i, square) => clearHighlight($(square)));
}

async function animateMovement(originElementImage, destinationElement) {
    const tempPiece = originElementImage.clone();
    tempPiece
        .css("position", "absolute")
        .css("left", originElementImage.offset().left)
        .css("top", originElementImage.offset().top)
        .css("width", originElementImage.width())
        .css("height", originElementImage.height())
        .css("z-index", 1);
    originElementImage.detach();

    tempPiece.appendTo("body");
    await tempPiece.animate({
        left: destinationElement.offset().left,
        top: destinationElement.offset().top
    }, 100).promise();

    destinationElement.find(".piece").remove();

    tempPiece.remove();
    originElementImage.css("left", "").css("top", "");
    originElementImage.appendTo(destinationElement);
}


function pieceSlice(pieces, capture = true) {
    const fromPiece = pieces[0].piece;

    pieces.shift();
    for (const [index, square] of pieces.entries()) {
        if (square.piece) return pieces.slice(0, fromPiece.color != square.piece.color && capture ? index + 1: index);
    }
    return pieces;
}

function straight(x1, y1, x2, y2) {
    let straightSlice;
    if (y1 == y2) straightSlice = board[y1].slice(Math.min(x1, x2), Math.max(x1, x2) + 1);
    else straightSlice = board.slice(Math.min(y1, y2), Math.max(y1, y2) + 1).map(column => column[x1]);

    if (straightSlice.at(-1) == board[y1][x1]) straightSlice.reverse();
    return straightSlice;
}

function diagonal(x1, y1, x2, y2) {
    let sliced = board.slice(Math.min(y1, y2), Math.max(y1, y2) + 1).map(column => {
        let columnSlice = column.slice(Math.min(x1, x2), Math.max(x1, x2) + 1);
        if (x1 > x2) columnSlice.reverse();
        return columnSlice;
    });

    if (y1 > y2) sliced.reverse();

    let diagonalSlice = [];
    for (const [index, _] of sliced.entries()) {
        let diagonalElement = sliced[index][index];
        if (!diagonalElement) break;
        diagonalSlice.push(diagonalElement);
    }
    if (diagonalSlice.at(-1) == board[y1][x1]) diagonalSlice.reverse();

    return diagonalSlice;
}

const straightMoves = (x, y) =>
        pieceSlice(straight(x, y, 0, y)).concat(
            pieceSlice(straight(x, y, boardWidth, y)),

            pieceSlice(straight(x, y, x, boardHeight)),
            pieceSlice(straight(x, y, x, 0))
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
    "knook": (x, y) => straightMoves(x, y).filter(move => move.piece).concat(horseMoves(x, y).filter(move => !move.piece)),
    "queen": (x, y) => diagonalMoves(x, y).concat(straightMoves(x, y)),
    "antiqueen": horseMoves,
    "archbishop": (x, y) => straightMoves(x, y).filter(move => {
        if (x == move.x) return Math.abs(y - move.y) % 2 == 0;
        else return Math.abs(x - move.x) % 2 == 0;
    }),
    "xook": diagonalMoves,
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
        if (piece.moved) return moves;

        for (const castleDirection of [0, boardWidth - 1]) {
            const castleRook = board[y][castleDirection];
            if (castleRook.piece.moved) continue;

            const between = straight(x, y, castleDirection, y);
            between.shift()
            between.pop();
            
            let castleMoves = []
            for (square of between) {
                if (square.piece && !(square == between[0] && square.piece.name == "bishop")) return moves;
                castleMoves.push(square)
            }
            moves = moves.concat(castleMoves);
        }
        return moves;
    },
    "child-pawn": (x, y) => pawnMoves(x, y, !board[y][x].piece.moved ? 2 : 1),
    "pawn": (x, y) => {
        let limit = 1;
        if (!board[y][x].piece.moved) {
            limit = 2;
            if ((boardWidth % 2 == 0 && (x == (boardWidth / 2) - 1 || x == boardWidth / 2)) || (board % 2 != 0 && x == Math.floor(boardWidth / 2))) limit = 3;
        }
        return pawnMoves(x, y, limit);
    }
};

// Arrow
arrows = {};
function drawArrow(fromElement, toElement) {
    const squareWidth = $(".square").width();

    let [y1, x1] = Object.values(fromElement.offset());
    let [y2, x2] = Object.values(toElement.offset());

    const canvas = document.createElement("canvas");
    canvas.style.top = Math.min(y1, y2) + "px";
    canvas.style.left = Math.min(x1, x2) + "px";
    canvas.height = Math.abs(y2 - y1) + squareWidth;
    canvas.width = (Math.abs(x2 - x1) / squareWidth) * squareWidth + squareWidth;
    document.body.appendChild(canvas);

    const squareOffset = squareWidth / 2;
    const canvasRect = canvas.getBoundingClientRect()
    y1 -= canvasRect.top;
    y1 += squareOffset

    x1 -= canvasRect.left;
    x1 += squareOffset;

    y2 -= canvasRect.top;
    y2 += squareOffset;

    x2 -= canvasRect.left;
    x2 += squareOffset;

    const viewportMin = Math.min($(window).width(), $(window).height());

    const context = canvas.getContext("2d");
    context.beginPath();

    context.lineWidth = percent(1.5, viewportMin);
    context.strokeStyle = "orange";
    context.fillStyle = "orange";
    context.lineCap = "round"
    
    context.moveTo(x1, y1);
    context.lineTo(x2, y2);
    context.stroke();

    context.save();
    context.beginPath();
        
    let radians = Math.atan((y2 - y1) / (x2 - x1));
    if (x1 == x2) radians += 90 * Math.PI / 180
    else radians += ((x2 > x1) ? 90 : -90) * Math.PI / 180;

    context.translate(x2, y2);
    context.rotate(radians);
    context.moveTo(0, 0);

    context.lineTo(percent(3, viewportMin), percent(5, viewportMin));
    context.lineTo(-percent(3, viewportMin), percent(5, viewportMin));

    context.closePath();
    context.restore();
    context.fill();

    fromID = fromElement.attr("id");
    toID = toElement.attr("id");
    if (fromID in arrows) arrows[fromID][toID] = canvas;
    else {
        arrows[fromID] = {};
        arrows[fromID][toID] = canvas;
    }
}

function clearArrow(fromElement, toElement) {
    const fromElementID = fromElement.attr("id");
    const toElementID = toElement.attr("id");
    arrows[fromElementID][toElementID].remove();
    delete arrows[fromElementID][toElementID];
}
function clearAllArrows() {
    arrows = {};
    $("canvas").remove();
}

var resizeTimeout;
$(window).on("resize", () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        const boardContainer = $("#board");
        const canvas = document.getElementsByTagName("canvas");
        canvas.width = boardContainer.width();
        canvas.height = boardContainer.height();

        const arrowsCopy = Object.assign({}, arrows);
        clearAllArrows();
        for (const [fromElementID, toElementIDs] of Object.entries(arrowsCopy)) {
            const fromElement = $(`#${fromElementID}`);
            for (const toElementID of Object.keys(toElementIDs)) drawArrow(fromElement, $(`#${toElementID}`));
        }
    }, 30);
});