const card = document.querySelector("#card");
const dropZone = document.querySelector("#drop-zone");

card.addEventListener("dragstart", e => {
    console.log(e);
})

dropZone.addEventListener("dragover", e => {
    e.preventDefault();
})

dropZone.addEventListener("drop", e => {
    dropZone.append(card)
})