from typing import Final

import numpy as np
import torch
from ultralytics import YOLO


class YoloBase:
    """
    Современная реализация YOLO.
    Использует ultralytics для обеспечения высокой скорости и точности.
    """

    def __init__(self, model_path: str = "yolo11n.pt") -> None:
        self.device: Final[str] = (
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.model = YOLO(model_path)
        self.model.to(self.device)

        self.class_names: list[str] = list(self.model.names.values())
        self.num_classes: int = len(self.class_names)

    def get_class_names(self) -> list[str]:
        return self.class_names

    def get_model(self) -> YOLO:
        return self.model

    def predict(
        self, frame: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Выполняет детекцию и возвращает данные в формате,
        совместимом с вашим RtspMergeServer.
        """
        results = self.model.predict(
            frame, conf=0.45, iou=0.5, verbose=False, device=self.device
        )  # Порог уверенности  # Порог NMS

        result = results[0]
        h, w = frame.shape[:2]

        boxes = []
        scores = []
        classes = []

        for box in result.boxes:
            # Координаты в пикселях [x1, y1, x2, y2]
            xyxy = box.xyxy[0].cpu().numpy()

            # Нормализация
            norm_box = [xyxy[0] / w, xyxy[1] / h, xyxy[2] / w, xyxy[3] / h]
            boxes.append(norm_box)

            scores.append(box.conf.item())
            classes.append(int(box.cls.item()))
            # ---------------------------

            # Возвращаем массивы
        return (
            np.array([boxes], dtype=np.float32),
            np.array([scores], dtype=np.float32),
            np.array([classes], dtype=np.float32),
            np.array([len(classes)], dtype=np.int32),
        )
