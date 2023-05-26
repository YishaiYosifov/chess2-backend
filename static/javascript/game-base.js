const squareHTML = $($.parseHTML(`
    <div class="square">
        <img class="img-fluid valid-move" src="../static/assets/valid-move.png" draggable="false">
    </div>
`));
const pieceHTML = $($.parseHTML(`<img class="img-fluid piece" draggable="false">`))

const gameToken = window.location.pathname.split("/").pop();
const CSSProperties = getComputedStyle(document.documentElement, null);

var gameData;
var moves;
var board;
var color;

var white;
var black;

var isGameOver = false;
var isLocalTurn;

var highlightElement;
var movingElement;

var allLegalCache = {};
var boardHeight;
var boardWidth;

var game;

const pieces = ["knook", "queen", "antiqueen", "rook", "horse", "xook", "bishop", "archbishop", "king", "pawn", "child-pawn"]

async function baseConstructBoard() {
    const boardContainer = $("#board");
    const userID = authInfo.user_id;

    gameData = await (await apiRequest("/game/get_game", {"game_token": gameToken})).json();
    
    white = await (await apiRequest(`/profile/${gameData["white"]}/get_info`, {"include": ["username", "country"]})).json();
    white["rating"] = await (await apiRequest(`/profile/${gameData["white"]}/get_ratings`, {"mode": gameData["mode"]})).json();

    black = await (await apiRequest(`/profile/${gameData["black"]}/get_info`, {"include": ["username", "country"]})).json();
    black["rating"] = await (await apiRequest(`/profile/${gameData["black"]}/get_ratings`, {"mode": gameData["mode"]})).json();

    color = userID == gameData.white ? "white" : "black";
    board = gameData.board;
    moves = gameData.moves;

    boardHeight = board.length;
    boardWidth = board[0].length;
    
    isLocalTurn = gameData.turn == userID;

    $(".profile-picture-white").attr("src", `../static/uploads/${gameData["white"]}/profile-picture.jpeg`)
    $(".profile-picture-black").attr("src", `../static/uploads/${gameData["black"]}/profile-picture.jpeg`)

    const promotionCard = $("#promotion-card");
    for (const piece of pieces) {
        if (["king", "pawn", "child-pawn"].includes(piece)) continue;

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
        if (gameData["is_over"]) return;
        if (isLocalTurn) enableDraggable();

        gameNamespace.on("move", this.socketioMove);
        gameNamespace.on("exception", this.socketioException);
        gameNamespace.on("game_over", this.socketioGameOver);

        $(`[color=${color}]`).mousedown(async function(event) {
            if (event.which != 1 || !isLocalTurn) return;
    
            $(".valid-move").hide().parent().droppable().droppable("disable");
        
            movingElement = $(this);
            const id = movingElement.parent().attr("id");
            let [y, x] = id.split("-");
            x = parseInt(x);
            y = parseInt(y);
        
            let legalMoves = allLegalCache[id] ?? await (await apiRequest("/game/get_legal", {"game_token": gameToken, "x": x, "y": y})).json();
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
    
            const promotionPiece = await new Promise((resolve, reject) => {
                function rejectFunction() {
                    if ($(this).is(destinationElement)) return;
                    $(".square").off("click", rejectFunction);
    
                    enableDraggable();
                    revertPiece(originElementImage);
                    promotionCard.fadeOut(300);
                    reject("Promotion Canceled");
                }

                $(".promotion-piece").click(function() {
                    promotionCard.fadeOut(300);
                    $(".square").off("click", rejectFunction);
                    resolve($(this).attr("id").split("-").at(-1));
                });
                $(".square").click(rejectFunction);
            });
            $(".promotion-piece").off("click");
            move_data["promote_to"] = promotionPiece;
        } else if (originSquare.piece.name == "king") {
            if (originY == destinationY && Math.abs(originX - destinationX) > 1) {
                if (originX > destinationX) destinationX = 1;
                else destinationX = 5;
            } else if (originX == destinationX && Math.abs(originY - destinationY) > 1) {
                if (originY > destinationY) destinationY = Math.floor(boardHeight / 2) - 1;
                else destinationY = Math.floor(boardHeight / 2);
                console.log(destinationY);
            }
        }
        Object.assign(move_data, {"origin_x": originX, "origin_y": originY, "destination_x": destinationX, "destination_y": destinationY});
    
        gameNamespace.emit("move", move_data);
    }

    async movePiece(moveLog, promoteTo) {
        movingElement = null;
        allLegalCache = {};
        moves.push(moveLog);

        for (const [index, capture] of Object.entries(moveLog["captured"])) {
            const capturedPieceImage = $(`#${capture.y}-${capture.x}`).find(".piece");
            capturedPieceImage.delay(index * 30).fadeOut(100, function() { $(this).remove(); });
            board[capture.y][capture.x].piece = null;
        }
        for (const move of moveLog["moved"]) {
            const [origin, destination] = [move["origin"], move["destination"]];
            const originPieceImage = $(`#${origin.y}-${origin.x}`).find(".piece");
            const destinationPiece = $(`#${destination.y}-${destination.x}`);

            const tempPiece = Object.assign({}, board[origin.y][origin.x].piece);
            if (move.piece.includes("pawn") && (destination.y == 0 || destination.y == boardHeight - 1)) {
                tempPiece.name = promoteTo;
                originPieceImage.attr("src", `../static/assets/pieces/${promoteTo}-${tempPiece.color}.png`);
            }

            board[origin.y][origin.x].piece = null;
            board[destination.y][destination.x].piece = tempPiece;
            
            animateMovement(originPieceImage, destinationPiece);
        }
    }

    async socketioGameOver(data) {
        isGameOver = true;
        disableDraggable();

        const gameOverModal = $("#game-over-modal");
        $("#game-over-reason-text").text("By " + data["reason"]);

        const whiteEloText = $("#white-elo-text");
        const blackEloText = $("#black-elo-text");
        if (data["white_results"] == 1) setWinner("white");
        else if (data["black_results"] == 1) setWinner("black");
        else {
            $("#game-over-results-text").text("DRAW")
            whiteEloText.addClass("bg-gray");
            blackEloText.addClass("bg-gray");
            gameOverModal.addClass("draw");
        }

        whiteEloText.text(white["rating"]);
        blackEloText.text(black["rating"]);

        gameOverModal.modal({backdrop: "static"});
        await gameOverModal.modal("show").promise();
        await sleep(450);

        await eloTextAnimation(whiteEloText, white["rating"], data["white_rating"]);
        eloTextAnimation(blackEloText, black["rating"], data["black_rating"]);
    }

    async socketioMove(data) {
        await game.movePiece(data["move_log"], data["promote_to"]);
    
        if (!data["is_over"] && data.turn == color) enableDraggable();
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

function setWinner(winner) {
    const loser = winner == "white" ? "black" : "white";
    $(`#${winner}-elo-text`).addClass("bg-success");
    $(`#${loser}-elo-text`).addClass("bg-danger");

    const isWinner = winner == color
    $("#game-over-modal").addClass(isWinner ? "victory" : "defeat");
    $("#game-over-results-text").text(isWinner ? "VICTORY" : "DEFEAT")
}

async function eloTextAnimation(textElement, currentElo, newElo) {
    const originalFont = textElement.css("font-size");
    await textElement.animate({"font-size": "25px"}, 500).promise();
    await sleep(300);

    const add = currentElo < newElo ? 1 : -1
    while (currentElo != newElo) {
        currentElo += add;
        textElement.text(currentElo);

        await sleep(50);
    }

    await sleep(300);
    textElement.animate({"font-size": originalFont}, 500);
}

function enableDraggable() {
    if (isGameOver) return;
    
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