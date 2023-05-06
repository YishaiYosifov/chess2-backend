function connect() { socket = io(location.origin); }
connect()

$(window).bind("beforeunload", () => { socket.disconnect(); });
$(window).bind("pageshow", e => {
    if (e.persisted) {
        socket.disconnect();
        socket = null;
        connect();
    }
})

socket.on("connect", () => { socket.emit("connected"); });

socket.on("game_started", game_data => { window.location.replace(`/game/${game_data["game_id"]}`); })
socket.on("incoming_games", game_data => { console.log(game_data); })