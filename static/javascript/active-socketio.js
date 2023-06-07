var socket;
var gameNamespace;

socket = io();
$(window).on("pageshow", (event) => {
    if (event.originalEvent.persisted) window.location.reload();
});

socket.on("game_started", gameData => window.location.replace(`/game/${gameData["game_id"]}`));
socket.on("incoming_games", gameData => console.log(gameData) );

socket.on("exception", data => console.error(data));