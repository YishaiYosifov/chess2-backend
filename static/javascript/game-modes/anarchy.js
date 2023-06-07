const pieces = ["knook", "queen", "antiqueen", "rook", "horse", "xook", "bishop", "archbishop", "king", "pawn", "child-pawn"]

async function anarchyConstructBoard() {
    const boardContainer = $("#board");

    const promotionCard = $("#promotion-card");
    for (const piece of pieces) {
        if (["king", "pawn", "child-pawn"].includes(piece)) continue;

        const image = $("<img></img>");
        image.addClass("img-fluid");
        image.addClass("promotion-piece");

        image.attr("id", `promotion-${piece}`);

        image.attr("draggable", "false");
        image.attr("src", `../static/assets/pieces/${piece}-${game.localUser.color}.webp`);
        image.appendTo(promotionCard);
    }

    let tempBoard = structuredClone(game.board);
    const colorMod = game.localUser.color == "white" ? 0 : 1
    if (game.localUser.color == "white") tempBoard.reverse();
    else {
        for (const element of $("#board-card").children()) $("#board-card").prepend(element);
    }

    for (const [rowIndex, row] of tempBoard.entries()) {
        for (const [columnIndex, column] of row.entries()) {
            let fixedRowIndex = rowIndex;
            if (game.localUser.color == "white") fixedRowIndex = game.boardHeight - fixedRowIndex - 1;

            const square = squareHTML.clone();
            square.attr("id", `${fixedRowIndex}-${columnIndex}`);
            square.addClass(((rowIndex + columnIndex) % 2 == colorMod) ? "square-light" : "square-dark");

            if (column.piece) {
                const piece = pieceHTML.clone();
                piece.attr("src", `../static/assets/pieces/${column.piece.name}-${column.piece.color}.webp`);
                piece.attr("color", column.piece.color);
                piece.appendTo(square)
            }

            boardContainer.append(square);
        }
    }
}

class Anarchy {
    constructor(gameData) {
        this.gameData = gameData;

        this.white = gameData.white;
        this.black = gameData.black;
        this.board = gameData.board;

        this.boardWidth = this.board[0].length;
        this.boardHeight = this.board.length;
        this.highlightElement;
        this.movingElement;

        this.legalMovesCache = gameData.client_legal_move_cache;
        this.isGameOver = gameData.is_over;
        this.moves = gameData.moves;

        this.turn = gameData.turn == this.white.user_id ? this.white : this.black;
        this.localUser = authInfo.user_id == this.white.user_id ? this.white : this.black;
        this.opponent = authInfo.user_id == this.white.user_id ? this.black : this.white;

        this.isLoading = true;
        this.moveLoadingBuffer = [];

        game = this;
        if (gameData.is_over) return;

        gameNamespace.on("move", this.socketioMove);
        gameNamespace.on("game_over", this.socketioGameOver);
        gameNamespace.on("exception", this.socketioException);
        gameNamespace.on("clock_sync", this.socketioSyncClock);
        gameNamespace.on("draw_request", drawRequest);

        gameNamespace.on("opponent_disconnected", opponentDisconnected);
        gameNamespace.on("opponent_connected", opponentConnected);
        gameNamespace.on("remote_connection", remoteConnection);
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
        const originSquare = game.board[originY][originX]
        if (originSquare.piece.name.includes("pawn") && (destinationY == game.board.length - 1 || destinationY == 0)) {
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
                if (originY > destinationY) destinationY = Math.floor(game.boardHeight / 2) - 1;
                else destinationY = Math.floor(game.boardHeight / 2);
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
        game.moves.push(moveLog);

        if (viewingMove == null) game.movingElement = null;

        for (const [index, capture] of Object.entries(moveLog["captured"])) {
            if (viewingMove == null) {
                const capturedPieceImage = $(`#${capture.y}-${capture.x}`).find(".piece");
                capturedPieceImage.delay(index * 30).fadeOut(100, function() { $(this).remove(); });
            }
            game.board[capture.y][capture.x].piece = null;
        }
        for (const move of moveLog["moved"]) {
            const [origin, destination] = [move["origin"], move["destination"]];
            const tempPiece = Object.assign({}, game.board[origin.y][origin.x].piece);
            if (viewingMove == null) {
                const originPieceImage = $(`#${origin.y}-${origin.x}`).find(".piece");
                const destinationPiece = $(`#${destination.y}-${destination.x}`);

                if (move.piece.includes("pawn") && (destination.y == 0 || destination.y == game.boardHeight - 1)) {
                    tempPiece.name = promoteTo;
                    originPieceImage.attr("src", `../static/assets/pieces/${promoteTo}-${tempPiece.color}.webp`);
                }
                animateMovement(originPieceImage, destinationPiece);
            }

            game.board[origin.y][origin.x].piece = null;
            game.board[destination.y][destination.x].piece = tempPiece;
        }
    }

    socketioSyncClock(data) {
        game.white.clock = data.white;
        game.black.clock = data.black;
        updateTimer();

        if (data.is_timeout) return;
        const timer = setInterval(() => {
            const isTimeout = updateTimer(game.turn);
            if (game.isGameOver || isTimeout) clearInterval(timer);
        }, 100);
    }

    async socketioGameOver(data) {
        $("#chat-active").fadeOut(100, () => $("#chat-over").fadeIn());
        
        game.isGameOver = true;
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

        whiteEloText.text(game.white["rating"]);
        blackEloText.text(game.black["rating"]);

        await gameOverModal.modal("show").promise();
        await sleep(450);

        if (game.white["rating"] != data["white_rating"]) await eloTextAnimation(whiteEloText, game.white["rating"], data["white_rating"]);
        if (game.black["rating"] != data["black_rating"]) eloTextAnimation(blackEloText, game.black["rating"], data["black_rating"]);
    }

    async socketioMove(data) {
        if (game.isLoading) {
            game.moveLoadingBuffer.push(data);
            return;
        }
        $(".stall-warning").hide();
        $(".clock").show();

        await game.movePiece(data["move_log"], data["promote_to"]);
        if (game.moves.length >= 2) $("#resign span").text("resign");
        game.legalMovesCache = data.legal_moves;
    
        game.turn = data.turn == "white" ? game.white : game.black;
        game.turn.turn_started_at = Date.now() / 1000;
        
        if (!data.is_over && game.turn == game.localUser) enableDraggable();
        else disableDraggable();
    }

    async socketioException(data) {
        console.error(data);
        if (game.turn == game.localUser) enableDraggable();
        if (game.movingElement) {
            revertPiece(game.movingElement);
            game.movingElement = null;
        }
    
        if (data["code"] == 5) {
            const forcedMoves = data["message"];
            for (let i = 0; i < 2; i++) {
                if (game.movingElement) return;

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
        if (event.which != 1 || game.turn != game.localUser || game.isGameOver || viewingMove != null) return;

        $(".valid-move").hide().parent().droppable().droppable("disable");
    
        game.movingElement = $(this);
        const id = game.movingElement.parent().attr("id");
        let [y, x] = id.split("-");
        x = parseInt(x);
        y = parseInt(y);

        let legalMoves = game.legalMovesCache[`(${x}, ${y})`] ?? [];
        for (const validMove of legalMoves) {
            const moveIndicator = $(`#${validMove.y}-${validMove.x}`).find(".valid-move");
            moveIndicator.fadeIn(300);
            
            moveIndicator.parent().droppable({drop: (event, ui) => game.moveListener($(ui.helper), $(event.target))}).droppable("enable");
        }
    }
}