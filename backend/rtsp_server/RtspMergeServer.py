import argparse
import datetime
import os
from typing import Any

import cv2
import numpy as np

from neural_net.NeuralNet import NeuralNetwork
from .RtspServer import RtspStreamer


class RtspMergeServer(RtspStreamer):
    def __init__(
        self,
        source: str | int = 0,
        fps: int = 30,
        port: int = 8554,
        host: str = "localhost",
        uri: str = "video",
        show_stat: bool = False,
        show_osd: bool = False,
        frame_skip: int = 0,
    ) -> None:
        self.model = NeuralNetwork()

        self.show_osd: bool = show_osd
        self.neural_osd: Any = None
        self.frame_skip: int = frame_skip
        self.frame_counter: int = 0
        self.active_class: dict[str, int] = {}

        self._activity_log: list[int] = []
        self._activity_log_last_time: float = 0.0

        self.supported_class: dict[str, bool] = {
            "person": True,
            "car": True,
            "bicycle": True,
            "motorbike": True,
            "bus": True,
            "truck": True,
            "boat": True,
            "backpack": True,
            "handbag": True,
            "cell phone": True,
        }

        # Вызов конструктора нового базового класса
        super().__init__(source=source, fps=fps, port=port, host=host, uri=uri, show_stat=show_stat)

    def frame_update(self, frame: np.ndarray) -> np.ndarray:
        """Переопределенный метод обработки кадра."""
        # 1. Добавляем временную метку
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if not self.show_osd:
            return frame

        # 2. Логика пропуска кадров для нейросети
        if self.frame_counter > self.frame_skip:
            self.frame_counter = 0

        if self.frame_counter == 0:
            self.neural_osd = self.model.detect_objects(frame)

        self.frame_counter += 1

        # 3. Отрисовка результатов
        if self.neural_osd is not None:
            frame = self.draw_outputs(frame, self.neural_osd, self.model.class_names, self.whitelist)

        return frame

    def draw_outputs(self, frame: np.ndarray, outputs: tuple, class_names: list[str], white_list: list[str] | None = None) -> np.ndarray:
        boxes, score, classes, nums = outputs
        # Извлекаем данные (предполагается формат [batch, num, data])
        boxes, score, classes, nums = boxes[0], score[0], classes[0], nums[0]

        wh: np.ndarray = np.flip(frame.shape[0:2])  # ширина и высота кадра
        current_active_class: dict[str, int] = {}

        for i in range(int(nums.item())):
            idx = int(classes[i].item())
            if idx >= len(class_names):
                continue

            cl = class_names[idx]

            if white_list is not None and cl not in white_list:
                continue

            current_active_class[cl] = current_active_class.get(cl, 0) + 1

            # Координаты (нормализованные -> пиксели)
            x1y1 = tuple((np.array(boxes[i][0:2]) * wh).astype(np.int32))
            x2y2 = tuple((np.array(boxes[i][2:4]) * wh).astype(np.int32))

            # Ограничение отрисовки границами кадра
            x1y1 = (max(0, x1y1[0]), max(0, x1y1[1]))
            text_pos = (x1y1[0], max(16, x1y1[1] + 16))

            cv2.rectangle(frame, x1y1, x2y2, (255, 0, 0), 2)
            score_val = score[i][0].item() if isinstance(score[i], (list, np.ndarray)) else score[i]
            label = f"{cl.capitalize()} {score_val:.2f}"
            cv2.putText(frame, label, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        self.active_class = current_active_class
        self.update_activity_log(current_active_class)

        return frame

    def update_activity_log(self, active_class: dict[str, int]) -> None:
        """Обновление истории активности (логов)."""
        log_fps = int(os.getenv("ACTIVITY_LOG_FPS", 1))
        log_length = int(os.getenv("ACTIVITY_LOG_LENGTH", 100))

        interval = 1.0 / log_fps
        now = datetime.datetime.now().timestamp()

        if (now - self._activity_log_last_time) < interval:
            return

        self._activity_log_last_time = now
        total_objects = sum(active_class.values())

        if len(self._activity_log) >= log_length:
            self._activity_log.pop(0)

        self._activity_log.append(total_objects)

    @property
    def activity_log(self) -> list[int]:
        return self._activity_log

    @property
    def whitelist(self) -> list[str]:
        return [cl for cl, enabled in self.supported_class.items() if enabled]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rtsp Neural Merge Server")
    parser.add_argument("--source", default=0, help="Video source (ID or URL)")
    parser.add_argument("--fps", default=30, type=int, help="Target FPS")
    parser.add_argument("--port", default=8554, type=int, help="RTSP Port")
    parser.add_argument("--host", default="localhost", help="MediaMTX Host")
    parser.add_argument("--uri", default="video", help="Stream URI")
    parser.add_argument("--stat", default=False, action="store_true", help="Show statistics")
    parser.add_argument("--osd", default=False, action="store_true", help="Show Neural OSD")
    parser.add_argument("--frame_skip", default=0, type=int, help="Frames to skip for AI")

    args = parser.parse_args()

    server = RtspMergeServer(source=args.source, fps=args.fps, port=args.port, host=args.host, uri=args.uri, show_stat=args.stat, show_osd=args.osd, frame_skip=args.frame_skip)

    server.start()
