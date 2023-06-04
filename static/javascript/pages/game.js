const squareHTML = $($.parseHTML(`
    <div class="square">
        <img class="img-fluid valid-move" src="../static/assets/valid-move.png" draggable="false">
    </div>
`));
const pieceHTML = $($.parseHTML(`<img class="img-fluid piece" draggable="false">`));

const gameToken = window.location.pathname.split("/").pop();
const CSSProperties = getComputedStyle(document.documentElement, null);

var animatingMovement = false;
var game;

async function main() {
    await loadAuthInfo();
    gameData = await (await apiRequest("/game/live/get_game", {"game_token": gameToken})).json();
    game = new Anarchy(gameData);
    $("#draw").prop("disabled", game.localUser.is_requesting_draw);
    if (game.opponent.is_requesting_draw) $("#draw-request").show();

    for (setColor of ["white", "black"]) {
        user = setColor == "white" ? game.white : game.black
        let userInfo = await (await apiRequest(`/profile/${user.user_id}/get_info`, {"include": ["username", "country_alpha"]})).json();
        userInfo["rating"] = await (await apiRequest(`/profile/${user.user_id}/get_ratings`, {"mode": gameData.mode})).json();
        Object.assign(user, userInfo);

        $(`.profile-picture-${setColor}`).attr("src", `../static/uploads/${user.user_id}/profile-picture.jpeg`);
        $(`.username-${setColor}`).append(user.username);
        $(`.country-${setColor}`).attr("src", `/assets/country/${user.country_alpha}`)
    }
    await anarchyConstructBoard();

    const pieceImages = $("#board").find("img");
    let loadedPieces = 0;
    pieceImages.on("load", () => {
        loadedPieces++;
        if (loadedPieces >= pieceImages.length) $("#board-loading").hide();
    }).each(function() {
        if (this.complete) $(this).trigger("load");
    })

    if (!game.isGameOver && game.turnColor == game.localUser.color) enableDraggable();
    if (!game.moves.length) $("#move-history-title").text("No Moves");
    if (game.moves.length < 2) $("#resign span").text("abort");
    
    if (game.isGameOver) updateTimer(null, gameData.ended_at)
    else {
        apiRequest("/game/live/sync_clock");
        const timer = setInterval(() => {
            updateTimer(game.turnColor);
            if (game.isGameOver) clearInterval(timer);
        }, 100);
    }

    game.moves.forEach(addMoveToTable);
    
    // Wait for profile pictures to load before setting board width
    const profilePictures = $(".profile-picture-white, .profile-picture-black");
    setBoardWidth();
    profilePictures.on("load", setBoardWidth);

    $(`[color=${game.localUser.color}]`).mousedown(game.mouseDownShowLegal);
    
    $(".square").mousedown(function(event) {
        if (event.which == 1) {
            clearAllHighlights();
            clearAllArrows();
        }
        else game.highlightElement = $(this);
    });
    $(".square").mouseup(function(event) {
        if (event.which == 1) return;

        const currentSquare = $(this);
        if (currentSquare.is(game.highlightElement)) {
            if (currentSquare.hasClass("highlight")) clearHighlight(currentSquare)
            else highlightSquare(currentSquare);
        } else {
            const highlightElementID = game.highlightElement.attr("id");
            const currentSquareID = currentSquare.attr("id");
            if (highlightElementID in arrows && currentSquareID in arrows[highlightElementID]) clearArrow(game.highlightElement, currentSquare);
            else drawArrow(game.highlightElement, currentSquare);
        }
    });

    $(".square").click(function() {
        if ($(this).find(".valid-move").is(":hidden") || game.isGameOver) return;
        game.moveListener(game.movingElement, $(this));
    });
}

$("#new-game").click(() => window.location.replace("/play?s=1"));
main();

function updateTimer(onlyFor = null, timestamp = null) {
    if (!timestamp) timestamp = Date.now() / 1000;
    
    if (!onlyFor || onlyFor == "white") $("#clock-white").text(formatSeconds(game.white.clock - timestamp));
    if (!onlyFor || onlyFor == "black") $("#clock-black").text(formatSeconds(game.black.clock - timestamp));
}

function setWinner(winner) {
    const loser = winner == "white" ? "black" : "white";
    $(`#${winner}-elo-text`).addClass("bg-success");
    $(`#${loser}-elo-text`).addClass("bg-danger");

    const isWinner = winner == game.localUser.color
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
    if (game.isGameOver) return;
    
    $(`img[color="${game.localUser.color}"]`).draggable({
        start: function(event, ui) { 
            $(this).draggable("option", "cursorAt", {
                left: Math.floor(this.clientWidth / 2),
                top: Math.floor(this.clientHeight / 2)
            }); 
        },
        containment: $("#board"),
        cursor: "grabbing",
        revert: "invalid",
        revertDuration: 100,
        zIndex: 1
    }).draggable("enable");
}

function disableDraggable() {
    $(".valid-move").hide();
    $(`img[color="${game.localUser.color}"]`).draggable().draggable("disable");
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
    animatingMovement = true;

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
    animatingMovement = false;
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

function setBoardWidth() {
    const windowHeight = $(window).height();
    const windowWidth = $(window).width();

    const boardCard = $("#board-card");
    const board = $("#board");

    const profile1 = $("#small-profile-white");
    const profile2 = $("#small-profile-black");

    if (windowWidth >= windowHeight || Math.abs(windowWidth - windowHeight) < 300) {
        profile1Height = profile1.height();
        profile2Height = profile2.height();
        maxHeight = 1111
        margin = 100;

        let height = windowHeight - $(".navbar").height() - profile1Height - profile2Height - margin;
        height = Math.max(370, height);
        height = Math.min(maxHeight, height);
        board.height(height);
        board.width(height * 0.80459770114);
    } else {
        let width = windowWidth - 70
        width = Math.min(550, width);
        width = Math.max(300, width);
        board.width(width);
        board.height(width * 1.24285714286);
    }

    const infoPanel = $("#info-panel");
    if (infoPanel.offset().top <= 100 || windowWidth - boardCard.width() >= 440) {
        infoPanel
            .removeClass("col-11")
            .addClass("col-4")
            .height(boardCard.height())
            .removeClass("mobile");
    }
    else {
        infoPanel
            .css("height", "")
            .width(boardCard.width() + 20)
            .addClass("mobile")
            .removeClass("col-4");
    }
}

var resizeTimeout;
$(window).on("resize", () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        setBoardWidth();
        
        const arrowsCopy = Object.assign({}, arrows);
        clearAllArrows();
        for (const [fromElementID, toElementIDs] of Object.entries(arrowsCopy)) {
            const fromElement = $(`#${fromElementID}`);
            for (const toElementID of Object.keys(toElementIDs)) drawArrow(fromElement, $(`#${toElementID}`));
        }
    }, 30);
});


// Move History
function addMoveToTable(move, i) {
    if (i == undefined) i = game.moves.length;
    i++;
    move = structuredClone(move);

    $("#move-history-title").text("Move History");
    let moveFormatted = "";

    if (move.moved[0].piece == "king" && (move.moved[1] && move.moved[1].piece == "rook")) {
        const king = move.moved[0];
        const rook = move.moved[1];

        if (king.origin.y == rook.origin.y) {
            if (rook.origin.x == 0) moveFormatted = "O-O";
            else moveFormatted = "O-O-O";
        } else {
            if (rook.origin.y > king.origin.y) moveFormatted = "🠙-O-O";
            else moveFormatted = "🠛-O-O";
        }
    } else {
        for (const moved of move.moved) {
            let isCapture = false
            for (const [i, captured] of Object.entries(move.captured)) {
                if (captured.x == moved.destination.x && captured.y == moved.destination.y) {
                    isCapture = true;
                    move.captured.splice(i)
                    break;
                }
            }

            let pieceChar;
            if (moved.piece == "knook") pieceChar = "KN";
            else if (moved.piece.includes("pawn")) pieceChar = isCapture ? numToLetter(moved.origin.x) : "";
            else pieceChar = moved.piece[0].toUpperCase();

            moveFormatted += `${pieceChar}${isCapture ? "x" : ""}${numToLetter(moved.destination.x)}${moved.destination.y + 1}`;
        }
    }
    
    for (const captured of move.captured) moveFormatted += `x${numToLetter(captured.x)}${captured.y + 1}`;
    
    const moveHistoryTable = $("#move-history-table");
    const columns = moveHistoryTable.children("tr");

    const lastColumn = columns.last();
    const lastMove = lastColumn.find("td:last-child");

    if (!lastColumn.length || lastMove.text()) {
        const column = $("<tr></tr>");
        column.append($(`<th scope="row">${columns.length + 1}</th>`));
        column.append($(`<td id="move-${i}">${moveFormatted}</td>`).click(revertToIndex));
        column.append($(`<td></td>`));
        moveHistoryTable.append(column);
    } else lastMove.text(moveFormatted).attr("id", `move-${i}`).click(revertToIndex);

    const tableHolder = $("#move-history-card").find(".card-body");
    tableHolder.scrollTop(tableHolder[0].scrollHeight);
}

var viewingMove = null;
$(window).on("keydown", e => {
    if (animatingMovement || !game.moves.length) return;
    
    let newViewingMove = viewingMove;
    if (e.key == "ArrowUp") {
        revertToIndex(0);
        return;
    } else if (e.key == "ArrowDown") {
        revertToIndex(game.moves.length);
        return;
    } else if (e.key == "ArrowLeft") {
        if (viewingMove == null) newViewingMove = game.moves.length;
        else if (viewingMove - 1 < 0) return;
        newViewingMove--;
        
        const move = game.moves[newViewingMove];
        for (const moved of move.moved) {
            animateMovement($(`#${moved.destination.y}-${moved.destination.x}`).find(".piece"), $(`#${moved.origin.y}-${moved.origin.x}`));
        }
        for (const captured of move.captured) {
            const piece = pieceHTML.clone();
            const color = newViewingMove % 2 == 0 ? "black" : "white";
            piece.attr("src", `../static/assets/pieces/${captured.piece}-${color}.png`);
            piece.attr("color", color);
            $(`#${captured.y}-${captured.x}`).append(piece);
        }
    } else if (e.key == "ArrowRight") {
        if (viewingMove == null || viewingMove >= game.moves.length) return;

        const move = game.moves[viewingMove];

        for (const captured of move.captured) {
            $(`#${captured.y}-${captured.x}`).find(".piece").remove()
        }
        for (const moved of move.moved) {
            animateMovement($(`#${moved.origin.y}-${moved.origin.x}`).find(".piece"), $(`#${moved.destination.y}-${moved.destination.x}`));
        }
        newViewingMove++;
    }
    else return;
    setViewingMove(newViewingMove);
});

function revertToIndex(moveIndex) {
    if (typeof(moveIndex) != "number") moveIndex = $(this).attr("id").split("-").at(-1);

    const revertBoard = structuredClone(game.board);
    for (const [i, move] of Object.entries(game.moves.slice(moveIndex).reverse())) {
        for (const moved of move.moved) {
            const destination = revertBoard[moved.destination.y][moved.destination.x];
            revertBoard[moved.origin.y][moved.origin.x].piece = Object.assign({}, destination.piece);
            destination.piece = null;
        }

        const pieceColor = i % 2 == game.moves.length % 2 ? "white" : "black";
        for (const captured of move.captured) revertBoard[captured.y][captured.x].piece = {"name": captured.piece, "color": pieceColor};
    }

    for (const row of revertBoard) {
        for (const square of row) {
            const squareElement = $(`#${square.y}-${square.x}`);
            squareElement.find(".piece").remove();
            if (square.piece && Object.keys(square.piece).length) {
                const piece = pieceHTML.clone();
                piece.attr("src", `../static/assets/pieces/${square.piece.name}-${square.piece.color}.png`);
                piece.attr("color", square.piece.color);
                if (square.piece.color == game.localUser.color) piece.mousedown(game.mouseDownShowLegal);

                squareElement.append(piece);
            }
        }
    }
    setViewingMove(moveIndex);
}

function setViewingMove(newViewingMove) {
    $("#move-history-table").find("td").css("border-bottom", "");

    if (newViewingMove < game.moves.length) {
        disableDraggable();
        $(`#move-${newViewingMove}`).css("border-bottom", "solid cornflowerblue");
        viewingMove = newViewingMove;
    } else {
        viewingMove = null;
        if (game.turnColor == game.localUser.color) enableDraggable();
    }
}

// Game Actions
$("#resign").click(async function() {
    if (await confirmAction($(this)) == "confirm") gameNamespace.emit("resign");
});
$("#draw").click(async function() {
    game.localUser.is_requesting_draw = true;
    if (await confirmAction($(this)) == "confirm") gameNamespace.emit("request_draw");
    else game.localUser.is_requesting_draw = false;
});

async function confirmAction(forElement) {
    const confirmationButtons = $("#game-actions-group").find("button");
    confirmationButtons.prop("disabled", true);

    const actionConfirmationCard = $("#action-confirmation");
    actionConfirmationCard
        .css("top", forElement.offset().top - actionConfirmationCard.height() - 10)
        .css("left", forElement.offset().left);
    await actionConfirmationCard.fadeIn(100).promise();

    function resetButtons() {
        actionConfirmationCard.fadeOut(100);
        $("#draw").prop("disabled", game.localUser.is_requesting_draw);
        $("#resign").prop("disabled", false);
    }

    return new Promise((resolve, reject) => {
        $(window).mousedown(reject)
        $("#cancel-action").mousedown(event => event.stopPropagation());
        $("#cancel-action").click(reject);

        $("#confirm-action").mousedown(event => event.stopPropagation());
        $("#confirm-action").click(event => {
            event.stopPropagation();
            resolve();
        });
    }).then(() => {
        resetButtons();
        return "confirm";
    }).catch(() => {
        resetButtons()
        return "cancel";
    });
}

// Draw Management
$("#accept-draw").click(() => {
    $("#draw-request").fadeOut(100);
    gameNamespace.emit("accept_draw");
});

$("#decline-draw").click(() => {
    $("#draw-request").fadeOut(100);
    gameNamespace.emit("decline_draw");
});

$("#ignore-draws").click(() => {
    $("#draw-request").fadeOut(100);
    gameNamespace.emit("ignore_draw_requests");
});

gameNamespace.on("draw_declined", () => {
    game.localUser.is_requesting_draw = false;
    $("#draw").prop("disabled", false);
});