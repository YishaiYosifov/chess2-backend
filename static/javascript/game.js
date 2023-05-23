async function main() {
    await loadAuthInfo()
    await baseConstructBoard();
    const game = new GameBase();
}
main()