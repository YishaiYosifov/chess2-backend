const socket = io(location.origin);

socket.on("connect", () => { socket.emit("connected"); });
socket.on("game_started", a => {
    console.log(a)
})