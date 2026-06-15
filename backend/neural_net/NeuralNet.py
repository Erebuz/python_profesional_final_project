import os
from typing import Any

import numpy as np

# Отключаем лишние логи движков
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from neural_net.yolobase import YoloBase


class NeuralNetwork:
    """
    Интерфейс нейронной сети для RtspMergeServer.
    """

    def __init__(self) -> None:
        self.neural_net = YoloBase(model_path="yolo11n.pt")

        self.model = self.neural_net.get_model()
        self.class_names = self.neural_net.get_class_names()

    def detect_objects(self, image: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Метод детекции.
        Принимает BGR кадр из OpenCV, возвращает предикты.
        """
        return self.neural_net.predict(image)
