const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

let drawing = false;

canvas.onmousedown = () => drawing = true;
canvas.onmouseup = () => drawing = false;

canvas.onmousemove = (e) => {
    if (!drawing) return;

    let x = e.offsetX;
    let y = e.offsetY;

    ctx.fillRect(x, y, 4, 4);

    socket.send(JSON.stringify({
        type: "draw",
        x, y,
        color: "black"
    }));
};

const socket = new WebSocket("ws://localhost:8000/ws/ROOM/USERNAME");

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "draw") {
        ctx.fillRect(data.x, data.y, 4, 4);
    }

    if (data.type === "timer") {
        document.getElementById("timer").innerText = data.time;
    }
};

function sendGuess() {
    let val = document.getElementById("guess").value;

    socket.send(JSON.stringify({
        type: "guess",
        guess: val
    }));
}