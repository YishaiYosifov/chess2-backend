const socket = io(location.origin);

socket.on("connect", () => { socket.emit("connected"); });

socket.on("game_started", game_data => { window.location.replace(`/game/${game_data["game_id"]}`); })
socket.on("incoming_game", game_data => { console.log(game_data); })