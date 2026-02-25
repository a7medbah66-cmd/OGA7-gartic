from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# 🗄️ In-memory storage
# =====================
users = {
    "admino": "a7med@1289"  # pre-loaded admin
}
sessions = {}
queue = []
rooms = {}

# =====================
# 📦 Models
# =====================
class User(BaseModel):
    username: str
    password: str

# =====================
# 🔐 AUTH
# =====================
@app.post("/register")
async def register(user: User):
    if user.username in users:
        return {"status": "error", "message": "User exists"}
    users[user.username] = user.password
    return {"status": "ok"}

@app.post("/login")
async def login(user: User):
    if users.get(user.username) != user.password:
        return {"status": "error", "message": "Invalid credentials"}
    token = str(uuid.uuid4())
    sessions[token] = user.username
    return {"status": "ok", "token": token}

# =====================
# 🎮 MATCHMAKING
# =====================
@app.post("/join_queue")
async def join_queue(token: str):
    username = sessions.get(token)
    if not username:
        return {"status": "error"}
    if username not in queue:
        queue.append(username)
    if len(queue) >= 2:
        p1 = queue.pop(0)
        p2 = queue.pop(0)
        room_id = str(uuid.uuid4())
        rooms[room_id] = {
            "players": [p1, p2],
            "connections": []
        }
        return {"status": "matched", "room": room_id}
    return {"status": "waiting"}

# =====================
# 🔌 WEBSOCKET
# =====================
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    if room_id not in rooms:
        await websocket.close()
        return
    rooms[room_id]["connections"].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for connection in rooms[room_id]["connections"]:
                if connection != websocket:
                    await connection.send_text(data)
    except WebSocketDisconnect:
        rooms[room_id]["connections"].remove(websocket)

# =====================
# 🌐 STATIC FILES
# =====================
if not os.path.exists("frontend"):
    os.makedirs("frontend")  # create folder if missing

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")