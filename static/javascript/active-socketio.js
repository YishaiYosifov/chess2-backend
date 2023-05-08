function connect() { socket = io(); }
connect();

$(window).bind("beforeunload", () => { socket.disconnect(); });
$(window).bind("pageshow", e => {
    if (e.persisted) {
        socket.disconnect();
        socket = null;
        connect();
    }
});

socket.on("connect", () => {
    socket.emit("connected");
    io("/game").emit("move", {"from_x": 0, "from_y": 2, "to_x": 0, "to_y": 3});
});

socket.on("game_started", game_data => { window.location.replace(`/game/${game_data["game_id"]}`); });
socket.on("incoming_games", game_data => { console.log(game_data); });

socket.on("exception", data => { alert(data); });