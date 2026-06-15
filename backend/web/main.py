import json
import os

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from web.auth import Auth


class WebServer:
    def __init__(self, app_logic):
        self.app = FastAPI(title="pp_smart_eye")
        self.logic = app_logic
        self.auth = Auth()
        self.sockets: list[WebSocket] = []

        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Static files
        self.public_path = os.path.join(app_logic.root, "public")
        if os.path.exists(os.path.join(self.public_path, "static")):
            self.app.mount("/static", StaticFiles(directory=os.path.join(self.public_path, "static")), name="static")

    async def send_all_sockets(self, data: dict):
        message = json.dumps(data)
        for socket in self.sockets:
            try:
                await socket.send_text(message)
            except:
                self.sockets.remove(socket)

    def setup_routes(self):
        from web.api_routes import router as api_router
        from web.auth_routes import router as auth_router
        from web.sys_routes import router as sys_router

        self.app.include_router(auth_router)
        self.app.include_router(api_router)
        self.app.include_router(sys_router)
