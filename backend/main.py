from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json

from game_manager import GameManager
from auth import register_user, login_user

app = FastAPI()
game = GameManager()

# =====================
# CORS (IMPORTANT)
# =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# SERVE FRONTEND
# =====================
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

# =====================
# REQUEST MODELS
# =====================
class AuthData(BaseModel):
    username: str
    password: str

class QueueData(BaseModel):
    username: str

# =====================
# AUTH ROUTES
# =====================
@app.post("/register")
async def register(data: AuthData):
    return register_user(data.username, data.password)

@app.post("/login")
async def login(data: AuthData):
    return login_user(data.username, data.password)

# =====================
# MATCHMAKING
# =====================
@app.post("/join_queue")
async def join_queue(data: QueueData):
    room_id = game.add_to_queue(data.username)
    return {"room": room_id}

# =====================
# WEBSOCKET
# =====================
@app.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(ws: WebSocket, room_id: str, username: str):
    await game.connect(ws, room_id, username)

    try:
        while True:
            data = await ws.receive_text()
            await game.handle_event(room_id, username, json.loads(data))

    except WebSocketDisconnect:
        await game.disconnect(room_id, username)