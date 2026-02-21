from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

router = APIRouter()

class WsManager:
    def __init__(self):
        self.connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, ws: WebSocket, group_id: int):
        await ws.accept()
        self.connections.setdefault(group_id, []).append(ws)

    def disconnect(self, ws: WebSocket, group_id: int):
        if group_id in self.connections:
            try: self.connections[group_id].remove(ws)
            except: pass

    async def broadcast(self, group_id: int, msg: dict):
        dead = []
        for ws in self.connections.get(group_id, []):
            try: await ws.send_json(msg)
            except: dead.append(ws)
        for d in dead:
            try: self.connections[group_id].remove(d)
            except: pass

manager = WsManager()

@router.websocket("/ws/{group_id}")
async def ws_endpoint(ws: WebSocket, group_id: int):
    await manager.connect(ws, group_id)
    try:
        while True:
            data = await ws.receive_text()
            if json.loads(data).get("type") == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(ws, group_id)
