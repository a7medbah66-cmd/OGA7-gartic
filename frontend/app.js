// 🔹 Use dynamic live URL
const API_BASE = window.location.origin; // Works both locally & deployed

let token = "";
let ws;
let roomId;

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

let drawing = false;

// =====================
// 🔐 AUTH
// =====================
async function register() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  const res = await fetch(`${API_BASE}/register`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({username, password})
  });

  const data = await res.json();
  alert(data.status === "ok" ? "Registered!" : data.message);
}

async function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({username, password})
  });

  const data = await res.json();

  if (data.status === "ok") {
    token = data.token;
    document.getElementById("auth").style.display = "none";
    document.getElementById("game").style.display = "block";
  } else {
    alert(data.message);
  }
}

// =====================
// 🎮 MATCHMAKING
// =====================
async function joinQueue() {
  const res = await fetch(`${API_BASE}/join_queue?token=${token}`, {
    method: "POST"
  });

  const data = await res.json();

  if (data.status === "matched") {
    roomId = data.room;
    connectWS();
    document.getElementById("status").innerText = "Matched! Start drawing!";
  } else {
    document.getElementById("status").innerText = "Waiting for player...";
  }
}

// =====================
// 🔌 WEBSOCKET
// =====================
function connectWS() {
  ws = new WebSocket(
    (location.protocol === "https:" ? "wss://" : "ws://") +
    location.host +
    `/ws/${roomId}`
  );

  ws.onmessage = (event) => {
    const {x, y} = JSON.parse(event.data);
    draw(x, y);
  };
}

// =====================
// 🎨 DRAWING
// =====================
canvas.addEventListener("mousedown", () => drawing = true);
canvas.addEventListener("mouseup", () => drawing = false);

canvas.addEventListener("mousemove", (e) => {
  if (!drawing || !ws) return;

  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  draw(x, y);
  ws.send(JSON.stringify({x, y}));
});

// Touch support
canvas.addEventListener("touchmove", (e) => {
  if (!ws) return;

  const rect = canvas.getBoundingClientRect();
  const x = e.touches[0].clientX - rect.left;
  const y = e.touches[0].clientY - rect.top;

  draw(x, y);
  ws.send(JSON.stringify({x, y}));
});

function draw(x, y) {
  ctx.fillRect(x, y, 4, 4);
}