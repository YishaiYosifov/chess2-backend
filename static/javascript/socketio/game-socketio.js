gameNamespace = io("/game");
gameNamespace.on("disconnect", () => {
    $("#disconnected").fadeIn(300)
    $("body").css("overflow", "hidden")
})