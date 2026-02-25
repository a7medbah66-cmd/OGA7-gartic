import random
import asyncio

WORDS = ["apple", "car", "house", "tree"]

class GameManager:
    def __init__(self):
        self.rooms = {}
        self.queue = []

    def add_to_queue(self, username):
        self.queue.append(username)

        if len(self.queue) >= 4:
            room_id = str(random.randint(1000, 9999))
            players = self.queue[:4]
            self.queue = self.queue[4:]

            self.rooms[room_id] = {
                "players": players,
                "sockets": {},
                "drawer_index": 0,
                "word": random.choice(WORDS),
                "scores": {p: 0 for p in players},
                "time": 60
            }

            return room_id

        return "waiting"

    async def connect(self, ws, room_id, username):
        await ws.accept()
        self.rooms[room_id]["sockets"][username] = ws

        await self.broadcast(room_id, {
            "type": "join",
            "players": self.rooms[room_id]["players"]
        })

        if len(self.rooms[room_id]["sockets"]) == len(self.rooms[room_id]["players"]):
            asyncio.create_task(self.start_game(room_id))

    async def disconnect(self, room_id, username):
        del self.rooms[room_id]["sockets"][username]

    async def broadcast(self, room_id, data):
        for ws in self.rooms[room_id]["sockets"].values():
            await ws.send_json(data)

    async def start_game(self, room_id):
        room = self.rooms[room_id]

        while True:
            drawer = room["players"][room["drawer_index"]]
            room["word"] = random.choice(WORDS)
            room["time"] = 60

            await self.broadcast(room_id, {
                "type": "round_start",
                "drawer": drawer,
                "word": room["word"]
            })

            # TIMER
            for t in range(60, 0, -1):
                await self.broadcast(room_id, {"type": "timer", "time": t})
                await asyncio.sleep(1)

            room["drawer_index"] = (room["drawer_index"] + 1) % len(room["players"])

    async def handle_event(self, room_id, username, data):
        room = self.rooms[room_id]

        if data["type"] == "draw":
            await self.broadcast(room_id, {
                "type": "draw",
                "x": data["x"],
                "y": data["y"],
                "color": data["color"]
            })

        elif data["type"] == "guess":
            if data["guess"].lower() == room["word"]:
                room["scores"][username] += 100
                await self.broadcast(room_id, {
                    "type": "correct",
                    "player": username
                })
            else:
                await self.broadcast(room_id, {
                    "type": "chat",
                    "player": username,
                    "msg": data["guess"]
                })