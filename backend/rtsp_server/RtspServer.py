import argparse
import os
import subprocess
import time
from threading import Thread
from typing import Any, Callable, Final, Optional

import cv2
import imageio_ffmpeg
import numpy as np


class RtspStreamer:
    """
    Класс для захвата видео и трансляции в RTSP сервер через FFmpeg.
    """

    def __init__(self, source: str | int = 0, fps: int = 30, port: int = 8554, uri: str = "video", host: str = "localhost", show_stat: bool = False) -> None:
        # Конфигурация
        self.source: str | int = source
        self.fps: int = fps
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
        ffmpeg_exe: str = imageio_ffmpeg.get_ffmpeg_exe()

        return [
            ffmpeg_exe,
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
            '-pix_fmt', 'yuv420p',
            '-profile:v', 'baseline',
            '-level', '3.0',

            '-f', 'rtsp',
            '-rtsp_transport', 'tcp',
            self.rtsp_url
        ]

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

    def start(self) -> None:
        """Запуск трансляции."""
        if not self.capture.isOpened():
            print(f"Error: Could not open source {self.source}")
            return

        self.is_running = True

        # Запускаем FFmpeg
        self._process = subprocess.Popen(self._get_ffmpeg_command(), stdin=subprocess.PIPE, stderr=subprocess.DEVNULL if not self.show_stat else None)

        # Поток статистики
        Thread(target=self._stats_loop, daemon=True).start()

        print(f"Stream started at {self.rtsp_url}")

        last_time = time.time()
        frame_duration = 1.0 / self.fps

        try:
            while self.is_running:
                start_loop = time.time()

                success, frame = self.capture.read()
                if not success:
                    print("Failed to read frame")
                    break

                # Обработка кадра
                frame = self.frame_update(frame)

                # Запись в пайп FFmpeg
                if self._process and self._process.stdin:
                    try:
                        self._process.stdin.write(frame.tobytes())
                    except BrokenPipeError:
                        print("FFmpeg process broken")
                        break

                # Расчет FPS
                end_loop = time.time()
                self.current_fps = round(1.0 / (end_loop - last_time))
                last_time = end_loop

                # Контроль частоты кадров
                sleep_time = frame_duration - (end_loop - start_loop)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            self.stop()

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
