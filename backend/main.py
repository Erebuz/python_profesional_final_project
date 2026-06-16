import asyncio
import os
from datetime import datetime
from threading import Thread

import uvicorn
from dotenv import load_dotenv

from rtsp_server.RtspMergeServer import RtspMergeServer
from web.main import WebServer


class App:
    def __init__(self):
        load_dotenv('.env')
        self.root = os.path.dirname(os.path.abspath(__file__))
        self.rtsp = RtspMergeServer(source=os.getenv("SOURCE", 0),
                                    port=int(os.getenv("RTSP_PORT", 8554)),
                                    host=os.getenv("RTSP_HOST", "localhost"),
                                    fps=30,
                                    show_stat=False,
                                    show_osd=False)

        print(f"DEBUG: Initializing RTSP Streamer")
        print(f"DEBUG: Source: {os.getenv("SOURCE", 0)}")
        print(f"DEBUG: Target: rtsp://{os.getenv("RTSP_HOST", "localhost")}:{os.getenv("RTSP_PORT", 8554)}/video")

        self.web_server = WebServer(self)

        load_dotenv(".env")

        # Передаем состояние
        self.web_server.app.state.rtsp = self.rtsp
        self.web_server.app.state.web_server = self.web_server
        self.web_server.app.state.root = self.root
        self.web_server.setup_routes()

    def start_rtsp(self):
        # OpenCV работает в отдельном потоке
        t = Thread(target=self.rtsp.start, daemon=True)
        t.start()

    async def broadcast_stats(self):
        """Фоновая задача для рассылки статистики по WebSockets"""
        while True:
            await asyncio.sleep(0.2)
            try:
                await self.web_server.send_all_sockets(
                    {
                        "action": "update",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "fps": {
                                "current": self.rtsp.current_fps,
                                "max": self.rtsp.fps_max,
                                "target": self.rtsp.target_fps,
                            },
                            "classes": self.rtsp.active_class,
                        },
                    }
                )
            except Exception as e:
                print(f"Broadcast error: {e}")

    async def main_async(self):
        """Главный асинхронный метод запуска"""
        self.start_rtsp()

        config = uvicorn.Config(app=self.web_server.app, host="0.0.0.0", port=8080, log_level="info")
        server = uvicorn.Server(config)

        stats_task = asyncio.create_task(self.broadcast_stats())

        await server.serve()

        stats_task.cancel()

    def run(self):
        """Точка входа, создающая цикл событий"""
        try:
            asyncio.run(self.main_async())
        except KeyboardInterrupt:
            print("Server stopped by user")


if __name__ == "__main__":
    app = App()
    app.run()
