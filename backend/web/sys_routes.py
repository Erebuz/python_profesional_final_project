import os

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

router = APIRouter()


@router.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    web_server = websocket.app.state.web_server
    await websocket.accept()
    web_server.sockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_json({"action": "pong"})
    except WebSocketDisconnect:
        if websocket in web_server.sockets:
            web_server.sockets.remove(websocket)


@router.get("/")
async def index(request: Request):
    index_path = os.path.join(request.app.state.root, "public", "index.html")
    if not os.path.exists(index_path):
        return {"error": "index.html not found"}
    return FileResponse(index_path)


@router.get("/{path_name:path}")
async def catch_all(request: Request, path_name: str):
    full_path = os.path.join(request.app.state.root, "public", path_name)

    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)

    return await index(request)
