var socket;
var gameNamespace;
function connect() {
    socket = io();
    gameNamespace = io("/game")
}
function disconnect() {
    socket.disconnect();
    gameNamespace.disconnect();
}
connect();

$(window).on("beforeunload", () => { disconnect(); });
$(window).on("pageshow", () => {
    if (performance.getEntriesByType("navigation")[0].type == "back_forward") {
        disconnect();
        connect();
    }
});

socket.on("connect", () => socket.emit("connected"));

socket.on("game_started", game_data => { window.location.replace(`/game/${game_data["game_id"]}`); });
socket.on("incoming_games", game_data => { console.log(game_data); });

socket.on("exception", data => { alert(data); });