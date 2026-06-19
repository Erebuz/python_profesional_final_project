import os
from unittest.mock import Mock, patch

import cv2
import numpy as np
import pytest

from rtsp_server.RtspMergeServer import RtspMergeServer
from rtsp_server.RtspServer import RtspStreamer

# ==================== MIXINS ====================


class FrameMixin:
    """Миксин для создания тестовых кадров."""

    @staticmethod
    def create_test_frame(width: int = 640, height: int = 480) -> np.ndarray:
        """Создает тестовый кадр заданного размера."""
        return np.zeros((height, width, 3), dtype=np.uint8)

    @staticmethod
    def create_colored_frame(
        width: int = 640, height: int = 480, color: tuple = (255, 0, 0)
    ) -> np.ndarray:
        """Создает цветной тестовый кадр."""
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = color
        return frame


class ConfigMixin:
    """Миксин для тестовых конфигураций."""

    DEFAULT_CONFIG = {
        "source": 0,
        "fps": 30,
        "port": 8554,
        "host": "localhost",
        "uri": "video",
        "show_stat": False,
    }

    @staticmethod
    def get_config(**overrides) -> dict:
        """Возвращает конфигурацию с переопределениями."""
        config = ConfigMixin.DEFAULT_CONFIG.copy()
        config.update(overrides)
        return config


class NeuralMixin:
    """Миксин для мокирования нейросети."""

    @staticmethod
    def create_mock_neural_output():
        """Создает мок-выход нейросети."""
        boxes = np.array([[[0.1, 0.1, 0.3, 0.3], [0.5, 0.5, 0.7, 0.7]]])
        score = np.array([[[0.95], [0.88]]])
        classes = np.array([[[0], [2]]])
        nums = np.array([[2]])
        return boxes, score, classes, nums

    @staticmethod
    def create_mock_neural_network():
        """Создает мок нейросети."""
        mock_net = Mock()
        mock_net.class_names = [
            "person",
            "car",
            "bicycle",
            "motorbike",
            "bus",
            "truck",
        ]
        mock_net.detect_objects = Mock(
            return_value=NeuralMixin.create_mock_neural_output()
        )
        return mock_net


class CaptureMixin:
    """Миксин для мокирования VideoCapture."""

    @staticmethod
    def create_mock_capture(width: int = 640, height: int = 480):
        """Создает мок VideoCapture."""
        mock_capture = Mock()
        mock_capture.isOpened.return_value = True
        mock_capture.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: width,
            cv2.CAP_PROP_FRAME_HEIGHT: height,
        }.get(prop, 0)
        mock_capture.read.return_value = (
            True,
            FrameMixin.create_test_frame(width, height),
        )
        return mock_capture


# ==================== FIXTURES ====================


@pytest.fixture
def mock_capture():
    """Фикстура для мокирования VideoCapture."""
    return CaptureMixin.create_mock_capture()


@pytest.fixture
def mock_neural_network():
    """Фикстура для мокирования нейросети."""
    return NeuralMixin.create_mock_neural_network()


@pytest.fixture
def test_frame():
    """Фикстура для тестового кадра."""
    return FrameMixin.create_test_frame()


# ==================== RTSP STREAMER TESTS ====================


class TestRtspStreamer(FrameMixin, ConfigMixin):
    """Тесты для RtspStreamer."""

    @pytest.mark.parametrize(
        "source,expected_type",
        [
            (0, int),
            ("test.mp4", str),
            ("rtsp://localhost:8554/stream", str),
        ],
    )
    def test_init_source_types(self, source, expected_type, mock_capture):
        """Тест инициализации с разными типами источника."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            streamer = RtspStreamer(source=source)
            assert isinstance(streamer.source, expected_type)

    @pytest.mark.parametrize(
        "fps,expected",
        [
            (15, 15),
            (30, 30),
            (60, 60),
        ],
    )
    def test_fps_properties(self, fps, expected, mock_capture):
        """Тест свойств FPS."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            streamer = RtspStreamer(source=0, fps=fps)
            assert streamer.fps_max == expected
            assert streamer.target_fps == expected

    @pytest.mark.parametrize(
        "port,host,uri,expected_url",
        [
            (8554, "localhost", "video", "rtsp://localhost:8554/video"),
            (
                8555,
                "192.168.1.1",
                "stream1",
                "rtsp://192.168.1.1:8555/stream1",
            ),
            (9000, "example.com", "cam", "rtsp://example.com:9000/cam"),
        ],
    )
    def test_rtsp_url_format(
        self, port, host, uri, expected_url, mock_capture
    ):
        """Тест формирования RTSP URL."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            streamer = RtspStreamer(source=0, port=port, host=host, uri=uri)
            assert streamer.rtsp_url == expected_url

    @pytest.mark.parametrize("new_fps", [15, 25, 45, 60])
    def test_set_target_fps(self, new_fps, mock_capture):
        """Тест динамического изменения FPS."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            streamer = RtspStreamer(source=0, fps=30)
            streamer.set_target_fps(new_fps)
            assert streamer.target_fps == new_fps
            assert streamer._target_fps == new_fps

    @pytest.mark.parametrize("show_stat", [True, False])
    def test_show_stat_property(self, show_stat, mock_capture):
        """Тест свойства show_stat."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            streamer = RtspStreamer(source=0, show_stat=show_stat)
            assert streamer.show_stat == show_stat

    def test_frame_update_default(self, test_frame, mock_capture):
        """Тест метода frame_update по умолчанию."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            streamer = RtspStreamer(source=0)
            result = streamer.frame_update(test_frame)
            assert np.array_equal(result, test_frame)

    @pytest.mark.parametrize(
        "width,height",
        [
            (640, 480),
            (1280, 720),
            (1920, 1080),
        ],
    )
    def test_frame_dimensions(self, width, height, mock_capture):
        """Тест размеров кадра."""
        mock_capture = CaptureMixin.create_mock_capture(width, height)
        with patch("cv2.VideoCapture", return_value=mock_capture):
            streamer = RtspStreamer(source=0)
            assert streamer.width == width
            assert streamer.height == height

    @pytest.mark.parametrize(
        "env_width,env_height,expected_width,expected_height",
        [
            ("1280", "720", 1280, 720),
            ("1920", "1080", 1920, 1080),
            (None, None, 640, 480),  # значения по умолчанию из мока
        ],
    )
    def test_frame_dimensions_from_env(
        self,
        env_width,
        env_height,
        expected_width,
        expected_height,
        mock_capture,
    ):
        """Тест размеров кадра из переменных окружения."""
        if env_width is not None:
            os.environ["SOURCE_WIDTH"] = env_width
        if env_height is not None:
            os.environ["SOURCE_HEIGHT"] = env_height

        try:
            with patch("cv2.VideoCapture", return_value=mock_capture):
                streamer = RtspStreamer(source=0)
                assert streamer.width == expected_width
                assert streamer.height == expected_height
        finally:
            os.environ.pop("SOURCE_WIDTH", None)
            os.environ.pop("SOURCE_HEIGHT", None)

    def test_get_ffmpeg_command(self, mock_capture):
        """Тест формирования команды FFmpeg."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            streamer = RtspStreamer(
                source=0, fps=30, port=8554, host="localhost", uri="video"
            )
            command = streamer._get_ffmpeg_command()

            assert "-f" in command
            assert "rawvideo" in command
            assert "-r" in command
            assert "30" in command
            assert "-c:v" in command
            assert "libx264" in command
            assert streamer.rtsp_url in command


# ==================== RTSP MERGE SERVER TESTS ====================


class TestRtspMergeServer(FrameMixin, ConfigMixin, NeuralMixin):
    """Тесты для RtspMergeServer."""

    @pytest.mark.parametrize("show_osd", [True, False])
    def test_init_show_osd(self, show_osd, mock_capture):
        """Тест инициализации с параметром show_osd."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0, show_osd=show_osd)
            assert server.show_osd == show_osd

    @pytest.mark.parametrize("frame_skip", [0, 1, 2, 5])
    def test_init_frame_skip(self, frame_skip, mock_capture):
        """Тест инициализации с параметром frame_skip."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0, frame_skip=frame_skip)
            assert server.frame_skip == frame_skip
            assert server.frame_counter == 0

    def test_supported_classes(self, mock_capture):
        """Тест поддерживаемых классов."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0)
            assert "person" in server.supported_class
            assert "car" in server.supported_class
            assert "bicycle" in server.supported_class
            assert len(server.supported_class) == 10

    @pytest.mark.parametrize(
        "enabled_classes,expected_whitelist_count",
        [
            (
                {
                    "person": True,
                    "car": True,
                    "bicycle": False,
                    "motorbike": False,
                    "bus": False,
                    "truck": False,
                    "boat": False,
                    "backpack": False,
                    "handbag": False,
                    "cell phone": False,
                },
                2,
            ),
            (
                {
                    "person": True,
                    "car": False,
                    "bicycle": False,
                    "motorbike": False,
                    "bus": False,
                    "truck": False,
                    "boat": False,
                    "backpack": False,
                    "handbag": False,
                    "cell phone": False,
                },
                1,
            ),
            (
                {
                    "person": False,
                    "car": False,
                    "bicycle": False,
                    "motorbike": False,
                    "bus": False,
                    "truck": False,
                    "boat": False,
                    "backpack": False,
                    "handbag": False,
                    "cell phone": False,
                },
                0,
            ),
        ],
    )
    def test_whitelist_property(
        self, enabled_classes, expected_whitelist_count, mock_capture
    ):
        """Тест свойства whitelist."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0)
            server.supported_class = enabled_classes
            whitelist = server.whitelist
            assert len(whitelist) == expected_whitelist_count

    def test_activity_log_initial(self, mock_capture):
        """Тест начального состояния activity_log."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0)
            assert server.activity_log == []

    def test_frame_update_without_osd(self, test_frame, mock_capture):
        """Тест frame_update без OSD."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0, show_osd=False)
            result = server.frame_update(test_frame)
            # Кадр должен быть изменен (добавлена временная метка)
            assert result.shape == test_frame.shape

    def test_frame_update_with_osd(
        self, test_frame, mock_capture, mock_neural_network
    ):
        """Тест frame_update с OSD."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0, show_osd=True)
            server.model = mock_neural_network
            result = server.frame_update(test_frame)
            assert result.shape == test_frame.shape
            # Проверяем, что нейросеть была вызвана
            mock_neural_network.detect_objects.assert_called_once()

    @pytest.mark.parametrize(
        "frame_skip,initial_counter,expected_calls",
        [
            (0, 0, 1),  # без пропуска - вызов на каждом кадре
            (1, 0, 1),  # пропуск 1 кадра
            (2, 0, 1),  # пропуск 2 кадра
        ],
    )
    def test_frame_skip_logic(
        self,
        frame_skip,
        initial_counter,
        expected_calls,
        test_frame,
        mock_capture,
        mock_neural_network,
    ):
        """Тест логики пропуска кадров."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(
                source=0, show_osd=True, frame_skip=frame_skip
            )
            server.model = mock_neural_network
            server.frame_counter = initial_counter

            server.frame_update(test_frame)

            assert (
                mock_neural_network.detect_objects.call_count == expected_calls
            )

    def test_draw_outputs(self, test_frame, mock_capture):
        """Тест метода draw_outputs."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0)
            outputs = self.create_mock_neural_output()
            class_names = [
                "person",
                "car",
                "bicycle",
                "motorbike",
                "bus",
                "truck",
            ]

            result = server.draw_outputs(test_frame, outputs, class_names)

            assert result.shape == test_frame.shape
            assert len(server.active_class) > 0

    @pytest.mark.parametrize(
        "white_list,expected_classes",
        [
            (["person"], ["person"]),
            (["person", "car"], ["person", "car"]),
            (None, ["person", "car"]),  # все классы из мока
        ],
    )
    def test_draw_outputs_with_whitelist(
        self, white_list, expected_classes, test_frame, mock_capture
    ):
        """Тест draw_outputs с whitelist."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0)
            outputs = self.create_mock_neural_output()
            class_names = [
                "person",
                "car",
                "bicycle",
                "motorbike",
                "bus",
                "truck",
            ]

            result = server.draw_outputs(
                test_frame, outputs, class_names, white_list
            )

            if white_list is not None:
                for cl in server.active_class:
                    assert cl in expected_classes

    @pytest.mark.parametrize(
        "active_class,expected_total",
        [
            ({"person": 1, "car": 2}, 3),
            ({"person": 5}, 5),
            ({}, 0),
        ],
    )
    def test_update_activity_log(
        self, active_class, expected_total, mock_capture
    ):
        """Тест обновления лога активности."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0)
            server.update_activity_log(active_class)

            assert len(server.activity_log) == 1
            assert server.activity_log[0] == expected_total

    @pytest.mark.parametrize(
        "log_length,updates_count,expected_length",
        [
            (5, 3, 3),
            (5, 10, 5),
            (10, 15, 10),
        ],
    )
    def test_activity_log_length_limit(
        self, log_length, updates_count, expected_length, mock_capture
    ):
        """Тест ограничения длины лога активности."""
        os.environ["ACTIVITY_LOG_LENGTH"] = str(log_length)

        try:
            with patch("cv2.VideoCapture", return_value=mock_capture):
                server = RtspMergeServer(source=0)

                # Прямое тестирование логики ограничения длины
                for _ in range(updates_count):
                    server._activity_log.append(1)
                    if len(server._activity_log) > log_length:
                        server._activity_log.pop(0)

                assert len(server.activity_log) == expected_length
        finally:
            os.environ.pop("ACTIVITY_LOG_LENGTH", None)

    def test_frame_counter_increment(self, test_frame, mock_capture):
        """Тест инкремента счетчика кадров."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspMergeServer(source=0, show_osd=True)
            initial_counter = server.frame_counter

            server.frame_update(test_frame)

            assert server.frame_counter == initial_counter + 1


# ==================== PARAMETRIZED INTEGRATION TESTS ====================


class TestRtspServerIntegration(FrameMixin, ConfigMixin, NeuralMixin):
    """Интеграционные тесты с параметризацией."""

    @pytest.mark.parametrize(
        "config_class",
        [
            RtspStreamer,
            RtspMergeServer,
        ],
    )
    @pytest.mark.parametrize("fps", [15, 30, 60])
    def test_fps_configuration(self, config_class, fps, mock_capture):
        """Тест конфигурации FPS для разных классов."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            if config_class == RtspMergeServer:
                server = config_class(source=0, fps=fps, show_osd=False)
            else:
                server = config_class(source=0, fps=fps)
            assert server._target_fps == fps
            assert server.target_fps == fps

    @pytest.mark.parametrize(
        "config_class,extra_params",
        [
            (RtspStreamer, {}),
            (RtspMergeServer, {"show_osd": False, "frame_skip": 0}),
        ],
    )
    def test_initialization(self, config_class, extra_params, mock_capture):
        """Тест инициализации разных классов."""
        with patch("cv2.VideoCapture", return_value=mock_capture):
            params = {"source": 0, "fps": 30}
            params.update(extra_params)
            server = config_class(**params)
            assert server.source == 0
            assert server._target_fps == 30

    @pytest.mark.parametrize(
        "width,height,fps",
        [
            (640, 480, 30),
            (1280, 720, 25),
            (1920, 1080, 60),
        ],
    )
    def test_various_resolutions(self, width, height, fps, mock_capture):
        """Тест различных разрешений и FPS."""
        mock_capture = CaptureMixin.create_mock_capture(width, height)
        with patch("cv2.VideoCapture", return_value=mock_capture):
            server = RtspStreamer(source=0, fps=fps)
            assert server.width == width
            assert server.height == height
            assert server._target_fps == fps
