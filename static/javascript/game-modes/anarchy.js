var highlightElement;
var movingElement;
var moves;

var allLegalCache = {};
var boardHeight;
var boardWidth;

var game;

const pieces = ["knook", "queen", "antiqueen", "rook", "horse", "xook", "bishop", "archbishop", "king", "pawn", "child-pawn"]

async function baseConstructBoard() {
    const boardContainer = $("#board");

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
    const colorMod = color == "white" ? 0 : 1
    if (color == "white") tempBoard.reverse();
    else {
        for (const element of $("#board-card").children()) $("#board-card").prepend(element);
    }

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

class Anarchy {
    constructor() {
        game = this;
        if (gameData["is_over"]) return;
        if (turnColor == color) enableDraggable();

        gameNamespace.on("move", this.socketioMove);
        gameNamespace.on("game_over", this.socketioGameOver);
        gameNamespace.on("exception", this.socketioException);
        gameNamespace.on("clock_sync", this.socketioSyncClock);

        $(`[color=${color}]`).mousedown(this.mouseDownShowLegal);
    
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
            if ($(this).find(".valid-move").is(":hidden") || isGameOver) return;
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
                if (originX > destinationX) destinationX = 2;
                else destinationX = 6;
            } else if (originX == destinationX && Math.abs(originY - destinationY) > 1) {
                if (originY > destinationY) destinationY = Math.floor(boardHeight / 2) - 1;
                else destinationY = Math.floor(boardHeight / 2);
            }
        } else if (["bishop", "xook"].includes(originSquare.piece.name)) {
            if (originX == destinationX) destinationY = originY + (originY > destinationY ? -2 : 2)
            else if (originY == destinationY) destinationX = originX + (originX > destinationX ? -2 : 2)
        }
        Object.assign(move_data, {"origin_x": originX, "origin_y": originY, "destination_x": destinationX, "destination_y": destinationY});
    
        gameNamespace.emit("move", move_data);
    }

    async movePiece(moveLog, promoteTo) {
        addMoveToTable(moveLog);
        moves.push(moveLog);

        if (viewingMove == null) movingElement = null;
        allLegalCache = {};

        for (const [index, capture] of Object.entries(moveLog["captured"])) {
            if (viewingMove == null) {
                const capturedPieceImage = $(`#${capture.y}-${capture.x}`).find(".piece");
                capturedPieceImage.delay(index * 30).fadeOut(100, function() { $(this).remove(); });
            }
            board[capture.y][capture.x].piece = null;
        }
        for (const move of moveLog["moved"]) {
            const [origin, destination] = [move["origin"], move["destination"]];
            const tempPiece = Object.assign({}, board[origin.y][origin.x].piece);
            if (viewingMove == null) {
                const originPieceImage = $(`#${origin.y}-${origin.x}`).find(".piece");
                const destinationPiece = $(`#${destination.y}-${destination.x}`);

                if (move.piece.includes("pawn") && (destination.y == 0 || destination.y == boardHeight - 1)) {
                    tempPiece.name = promoteTo;
                    originPieceImage.attr("src", `../static/assets/pieces/${promoteTo}-${tempPiece.color}.png`);
                }
                animateMovement(originPieceImage, destinationPiece);
            }

            board[origin.y][origin.x].piece = null;
            board[destination.y][destination.x].piece = tempPiece;
        }
    }

    socketioSyncClock(data) {
        white.clock = data.white;
        black.clock = data.black;
        updateTimer();
    }

    async socketioGameOver(data) {
        isGameOver = true;
        disableDraggable();

        const gameOverModal = $("#game-over-modal");
        $("#game-over-reason-text").text(data["reason"]);

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

        if (white["rating"] != data["white_rating"]) await eloTextAnimation(whiteEloText, white["rating"], data["white_rating"]);
        if (black["rating"] != data["black_rating"]) eloTextAnimation(blackEloText, black["rating"], data["black_rating"]);
    }

    async socketioMove(data) {
        await game.movePiece(data["move_log"], data["promote_to"]);
    
        turnColor = data.turn;
        if (!data.is_over && data.turn == color) enableDraggable();
        else disableDraggable();
    }

    async socketioException(data) {
        console.error(data);
        if (turnColor == color) enableDraggable();
        if (movingElement) {
            revertPiece(movingElement);
            movingElement = null;
        }
    
        if (data["code"] == 5) {

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

    async mouseDownShowLegal(event) {
        if (event.which != 1 || turnColor != color || isGameOver || viewingMove != null) return;

        $(".valid-move").hide().parent().droppable().droppable("disable");
    
        movingElement = $(this);
        const id = movingElement.parent().attr("id");
        let [y, x] = id.split("-");
        x = parseInt(x);
        y = parseInt(y);
    
        let legalMoves = allLegalCache[id] ?? await (await apiRequest("/game/live/get_legal", {"game_token": gameToken, "x": x, "y": y})).json();
        allLegalCache[id] = legalMoves;
        for (const validMove of legalMoves) {
            const moveIndicator = $(`#${validMove.y}-${validMove.x}`).find(".valid-move");
            moveIndicator.fadeIn(300);
            
            moveIndicator.parent().droppable({drop: (event, ui) => game.moveListener($(ui.helper), $(event.target))}).droppable("enable");
        }
    }
}