const socket = io(location.origin);

socket.on("connect", () => { socket.emit("connected"); });