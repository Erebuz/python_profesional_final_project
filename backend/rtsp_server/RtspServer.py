import argparse
import os
import shutil
import socket
import subprocess
import time
from threading import Thread
from typing import Final, Optional

import cv2
import numpy as np
import imageio_ffmpeg


class RtspStreamer:
    """
    Класс для захвата видео и трансляции в RTSP сервер через FFmpeg.
    """

    def __init__(self, source: str | int = 0, fps: int = 30, port: int = 8554, uri: str = "video", host: str = "localhost", show_stat: bool = False) -> None:
        # Конфигурация
        self.source: str | int = source
        self.fps: int = fps
        self.port: int = port
        self.uri: str = uri
        self.host: str = host
        self.rtsp_url: Final[str] = f"rtsp://{host}:{port}/{uri}"
        print('RTSP output:', self.rtsp_url)
        self.show_stat: bool = show_stat

        # Захват видео
        self.capture: cv2.VideoCapture = cv2.VideoCapture(self.source)

        # Получаем размеры кадра
        self.width: int = int(os.getenv("SOURCE_WIDTH", self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        self.height: int = int(os.getenv("SOURCE_HEIGHT", self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        self.frame: Optional[np.ndarray] = None
        self.is_running: bool = False
        self.current_fps: float = 0.0

        # Процесс FFmpeg
        self._process: Optional[subprocess.Popen] = None

    @property
    def fps_max(self) -> int:
        return self.fps

    @property
    def target_fps(self) -> int:
        return self.fps

    def set_target_fps(self, val: int) -> None:
        """Метод для динамического изменения FPS (используется в API)"""
        self.fps = val
        print(f"Target FPS updated to: {val}")

    def _get_ffmpeg_command(self) -> list[str]:
        """Формирует команду FFmpeg для трансляции."""
        ffmpeg_bin = shutil.which("ffmpeg")

        # 2. Если системного нет (Windows разработка), берем из imageio_ffmpeg
        if not ffmpeg_bin:
            try:
                ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                ffmpeg_bin = "ffmpeg"

        cmd = [ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-y"]

        if isinstance(self.source, str) and not self.source.isdigit() and os.path.isfile(self.source):
            cmd.append("-re")

        cmd.extend([
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f"{self.width}x{self.height}",
            '-r', str(self.fps),
            '-i', '-',

            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            "-g", str(self.fps * 2),
            "-x264-params", "keyint=" + str(self.fps * 2) + ":min-keyint=" + str(self.fps * 2) + ":scenecut=0",

            '-pix_fmt', 'yuv420p',
            '-profile:v', 'baseline',
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp',
            self.rtsp_url
        ])

        return cmd

    def frame_update(self, frame: np.ndarray) -> np.ndarray:
        """Метод для обработки кадров (можно переопределить)."""
        return frame

    def _stats_loop(self) -> None:
        """Вывод статистики в консоль."""
        while self.is_running:
            if self.show_stat:
                os.system("cls" if os.name == "nt" else "clear")
                print(f"--- Stream Stats ---")
                print(f"Target: {self.rtsp_url}")
                print(f"Res:    {self.width}x{self.height}")
                print(f"FPS:    {self.current_fps:.2f}")
            time.sleep(1)

    def _wait_for_server(self, timeout: int = 30) -> bool:
        """Ожидание доступности RTSP сервера."""
        print(f"[*] Waiting for RTSP server at {self.host}:{self.port}...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((self.host, self.port), timeout=1):
                    print("[+] RTSP server is reachable.")
                    return True
            except (ConnectionRefusedError, socket.timeout):
                time.sleep(1)
        return False

    def start(self) -> None:
        """Запуск трансляции."""
        if not self.capture.isOpened():
            print(f"Error: Could not open source {self.source}")
            return

        success, first_frame = self.capture.read()
        if not success or first_frame is None:
            print("Error: Could not read the first frame to determine resolution.")
            return

        if not self._wait_for_server():
            print(f"Error: MediaMTX ({self.host}) not found. Check docker-compose.")
            return

        self.height, self.width = first_frame.shape[:2]
        print(f"[*] Detected resolution: {self.width}x{self.height}")
        print(f"[*] Target URL: {self.rtsp_url}")

        cmd = self._get_ffmpeg_command()
        print(f"[*] Starting FFmpeg with command: {' '.join(cmd)}")

        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=None,
            stderr=subprocess.STDOUT,
            bufsize=0
        )

        self.is_running = True

        Thread(target=self._stats_loop, daemon=True).start()

        last_time = time.time()
        frame_duration = 1.0 / self.fps

        try:
            self._send_frame(first_frame)

            while self.is_running:
                start_loop = time.time()

                success, frame = self.capture.read()
                if not success:
                    if isinstance(self.source, str):
                        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        print("Source stream stopped.")
                        break

                self._send_frame(frame)

                end_loop = time.time()
                self.current_fps = round(1.0 / (end_loop - last_time)) if (end_loop - last_time) > 0 else 0
                last_time = end_loop

                sleep_time = frame_duration - (end_loop - start_loop)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            self.stop()

    def _send_frame(self, frame: np.ndarray) -> None:
        """Вспомогательный метод для отправки кадра в stdin FFmpeg."""
        if not self._process or not self._process.stdin:
            return

        try:
            frame = self.frame_update(frame)

            if frame.shape[0] != self.height or frame.shape[1] != self.width:
                frame = cv2.resize(frame, (self.width, self.height))

            self._process.stdin.write(frame.tobytes())
        except BrokenPipeError:
            print("[!!!] FFmpeg process broken (BrokenPipe). Check logs above for FFmpeg errors.")
            self.is_running = False
        except Exception as e:
            print(f"Error sending frame: {e}")
            self.is_running = False

    def stop(self) -> None:
        """Остановка всех процессов."""
        self.is_running = False
        if self.capture:
            self.capture.release()
        if self._process:
            if self._process.stdin:
                self._process.stdin.close()
            self._process.terminate()
            self._process.wait()
        print("Stream stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FFmpeg RTSP Producer")
    parser.add_argument("--source", default=0, help="Device ID or video file")
    parser.add_argument("--fps", default=30, type=int, help="Target FPS")
    parser.add_argument("--port", default=8554, type=int, help="RTSP Port")
    parser.add_argument("--host", default="localhost", help="RTSP Server Host (e.g. mediamtx)")
    parser.add_argument("--uri", default="video", help="Stream URI")
    parser.add_argument("--stat", action="store_true", help="Show statistics")

    args = parser.parse_args()

    streamer = RtspStreamer(source=args.source, fps=args.fps, port=args.port, host=args.host, uri=args.uri, show_stat=args.stat)
    streamer.start()
