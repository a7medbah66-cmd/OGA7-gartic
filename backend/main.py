from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid, asyncio, random, os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# In-memory storage
# -------------------------
users = {"admino": "a7med@1289"}  # admin user
sessions = {}  # token -> username

rooms = {}  # room_id -> room_data

# -------------------------
# Models
# -------------------------
class User(BaseModel):
    username: str
    password: str = None

# -------------------------
# Auth endpoints
# -------------------------
@app.post("/login")
async def login(user: User):
    if user.username == "admino":
        # Admin requires password
        if users.get("admino") != user.password:
            return {"status": "error", "message": "Invalid credentials"}
        token = str(uuid.uuid4())
        sessions[token] = user.username
        return {"status": "ok", "token": token, "username": user.username, "is_admin": True}

    # Normal user: no password needed
    token = str(uuid.uuid4())
    sessions[token] = user.username
    return {"status": "ok", "token": token, "username": user.username, "is_admin": False}

# -------------------------
# Admin endpoints
# -------------------------
@app.post("/create_room")
async def create_room(token: str, rounds: int = 3, time_limit: int = 20):
    username = sessions.get(token)
    if username != "admino":
        return {"status": "error", "message": "Unauthorized"}

    room_id = str(uuid.uuid4())
    rooms[room_id] = {
        "players": [],
        "spectators": [],
        "round": 0,
        "word": "",
        "connections": [],
        "scores": {},
        "time_limit": time_limit,
        "rounds_total": rounds,
        "drawing_player": None
    }
    return {"status":"ok", "room_id": room_id}

# -------------------------
# Join room (auto-join for users)
# -------------------------
@app.post("/join_room")
async def join_room(token: str):
    username = sessions.get(token)
    if not username:
        return {"status": "error"}

    # Auto-join the first room available
    if not rooms:
        return {"status":"error", "message":"No room created yet"}
    room_id = list(rooms.keys())[0]
    room = rooms[room_id]

    if username not in room["players"]:
        room["players"].append(username)
        room["scores"][username] = 0

    return {"status":"ok", "room_id": room_id}

# -------------------------
# WebSocket for real-time
# -------------------------
WORDS = ["apple", "banana", "cat", "dog", "house", "tree", "car", "star", "sun", "moon"]

@app.websocket("/ws/{room_id}/{token}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str):
    username = sessions.get(token)
    if not username or room_id not in rooms:
        await websocket.close()
        return

    room = rooms[room_id]
    await websocket.accept()
    room["connections"].append({"ws": websocket, "user": username})

    try:
        while True:
            data = await websocket.receive_json()

            # Handle drawing
            if data.get("type") == "draw":
                for c in room["connections"]:
                    if c["ws"] != websocket:
                        await c["ws"].send_json({"type":"draw","x":data["x"],"y":data["y"]})

            # Handle guesses
            if data.get("type") == "guess":
                guess = data.get("guess")
                if guess == room["word"] and username != room.get("drawing_player"):
                    room["scores"][username] += 100
                    for c in room["connections"]:
                        await c["ws"].send_json({
                            "type":"guess_correct",
                            "user": username
                        })
                else:
                    # Broadcast normal chat
                    for c in room["connections"]:
                        await c["ws"].send_json({"type":"chat","user":username,"message":guess})

            # Admin can start next round
            if data.get("type")=="next_round" and username=="admino":
                await start_next_round(room_id)

    except WebSocketDisconnect:
        room["connections"] = [c for c in room["connections"] if c["ws"]!=websocket]

# -------------------------
# Round handling
# -------------------------
async def start_next_round(room_id):
    room = rooms[room_id]
    room["round"] += 1
    if room["round"] > room["rounds_total"]:
        # Game finished
        for c in room["connections"]:
            await c["ws"].send_json({"type":"game_over","scores":room["scores"]})
        return
    # pick drawer
    room["drawing_player"] = random.choice(room["players"])
    room["word"] = random.choice(WORDS)
    for c in room["connections"]:
        await c["ws"].send_json({
            "type":"new_round",
            "round": room["round"],
            "total_rounds": room["rounds_total"],
            "drawer": room["drawing_player"],
            "time_limit": room["time_limit"]
        })
    # start countdown
    asyncio.create_task(round_timer(room_id, room["time_limit"]))

async def round_timer(room_id, time_left):
    room = rooms[room_id]
    for t in range(time_left,0,-1):
        for c in room["connections"]:
            await c["ws"].send_json({"type":"timer","time":t})
        await asyncio.sleep(1)
    await start_next_round(room_id)

# -------------------------
# Serve frontend
# -------------------------
if not os.path.exists("frontend"):
    os.makedirs("frontend")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")