const squareHTML = $($.parseHTML(`
    <div class="square">
        <img class="img-fluid valid-move" src="../static/assets/valid-move.png" draggable="false">
    </div>
`));
const pieceHTML = $($.parseHTML(`<img class="img-fluid piece" draggable="false">`));
const moveTableItem = $($.parseHTML(`

`))

const gameToken = window.location.pathname.split("/").pop();
const CSSProperties = getComputedStyle(document.documentElement, null);

var gameData;
var board;

var turnColor;
var white;
var black;

var animatingMovement = false;
var isGameOver = false;

async function main() {
    await loadAuthInfo()
    const userID = authInfo.user_id;
    gameData = await (await apiRequest("/game/live/get_game", {"game_token": gameToken})).json();
    
    white = await (await apiRequest(`/profile/${gameData.white.user_id}/get_info`, {"include": ["username", "country_alpha"]})).json();
    white["rating"] = await (await apiRequest(`/profile/${gameData.white.user_id}/get_ratings`, {"mode": gameData.mode})).json();
    white = Object.assign(white, gameData.white);

    black = await (await apiRequest(`/profile/${gameData.black.user_id}/get_info`, {"include": ["username", "country_alpha"]})).json();
    black["rating"] = await (await apiRequest(`/profile/${gameData.black.user_id}/get_ratings`, {"mode": gameData.mode})).json();
    black = Object.assign(black, gameData.black);

    color = userID == black.user_id ? "black" : "white";
    turnColor = gameData.turn == white.user_id ? "white" : "black";
    isGameOver = gameData.is_over;

    board = gameData.board;
    moves = gameData.moves;
    if (!moves.length) $("#move-history-title").text("No Moves");

    boardHeight = board.length;
    boardWidth = board[0].length;
    
    await baseConstructBoard();
    if (isGameOver) updateTimer(null, gameData.ended_at)
    else {
        apiRequest("/game/live/sync_clock");
        const timer = setInterval(() => {
            updateTimer(turnColor);
            if (isGameOver) clearInterval(timer);
        }, 100);
    }
    for (setColor of ["white", "black"]) {
        user = setColor == "white" ? white : black
        $(`.profile-picture-${setColor}`).attr("src", `../static/uploads/${user.user_id}/profile-picture.jpeg`);
        $(`.username-${setColor}`).append(user.username);
        $(`.country-${setColor}`).attr("src", `/assets/country/${user.country_alpha}`)
    }

    const profilePictures = $(".profile-picture-white, .profile-picture-black");
    const totalPictures = profilePictures.length;
    let loaded = 0;
    profilePictures.on("load", function() {
        loaded++;
        if (loaded === totalPictures) {
            setBoardWidth();
            moves.forEach(addMoveToTable)
        }
    });
    const game = new Anarchy();
}

$("#new-game").click(() => window.location.replace("/play?s=1"));
main();

function updateTimer(onlyFor = null, timestamp = null) {
    if (!timestamp) timestamp = Date.now() / 1000;
    
    if (!onlyFor || onlyFor == "white") $("#clock-white").text(formatSeconds(white.clock - timestamp));
    if (!onlyFor || onlyFor == "black") $("#clock-black").text(formatSeconds(black.clock - timestamp));
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
    
    $(`img[color="${color}"]`).draggable({
        containment: $("#board"),
        cursor: "grabbing",
        revert: "invalid",
        revertDuration: 100,
        zIndex: 1
    }).draggable("enable");
}

function disableDraggable() {
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
    if (i == undefined) i = moves.length;
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
    if (animatingMovement || !moves) return;
    
    let newViewingMove = viewingMove;
    if (e.key == "ArrowUp") {
        revertToIndex(0);
        return;
    } else if (e.key == "ArrowDown") {
        revertToIndex(moves.length);
        return;
    } else if (e.key == "ArrowLeft") {
        if (viewingMove == null) newViewingMove = moves.length;
        else if (viewingMove - 1 < 0) return;

        disableDraggable()
        newViewingMove--;
        
        const move = moves[newViewingMove];
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
        if (viewingMove == null || viewingMove >= moves.length) return;

        const move = moves[viewingMove];

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
    setViewingMove(moveIndex);

    const revertBoard = structuredClone(board);
    for (const [i, move] of Object.entries(moves.slice(moveIndex).reverse())) {
        for (const moved of move.moved) {
            const destination = revertBoard[moved.destination.y][moved.destination.x];
            revertBoard[moved.origin.y][moved.origin.x].piece = Object.assign({}, destination.piece);
            destination.piece = null;
        }

        const pieceColor = i % 2 == moves.length % 2 ? "white" : "black";
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
                squareElement.append(piece);
            }
        }
    }
}

function setViewingMove(newViewingMove) {
    $("#move-history-table").find("td").css("border-bottom", "");

    if (newViewingMove < moves.length) {
        disableDraggable();
        $(`#move-${newViewingMove}`).css("border-bottom", "solid cornflowerblue");
        viewingMove = newViewingMove;
    } else {
        viewingMove = null;
        enableDraggable();
    }
}