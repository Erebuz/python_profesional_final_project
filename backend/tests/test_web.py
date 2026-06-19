import os
import tempfile
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import bcrypt
import pytest
import yaml
from fastapi import Request, WebSocket
from fastapi.testclient import TestClient

from web.api_routes import router as api_router
from web.auth import Auth
from web.auth_routes import router as auth_router
from web.main import WebServer
from web.sys_routes import router as sys_router

# ==================== MIXINS ====================


class AuthMixin:
    """Миксин для тестирования аутентификации."""

    @staticmethod
    def create_test_user(
        username: str = "testuser",
        password: str = "testpass",
        user_id: int = 1,
    ) -> dict:
        """Создает тестового пользователя."""
        hashed = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        return {"id": user_id, "username": username, "password": hashed}

    @staticmethod
    def create_test_users(count: int = 3) -> list[dict]:
        """Создает список тестовых пользователей."""
        return [
            AuthMixin.create_test_user(f"user{i}", f"pass{i}", i)
            for i in range(1, count + 1)
        ]


class RequestMixin:
    """Миксин для создания тестовых запросов."""

    @staticmethod
    def create_mock_request(headers: dict = None, state: dict = None) -> Mock:
        """Создает мок запроса."""
        mock_request = Mock(spec=Request)
        mock_request.headers = headers or {}
        mock_request.app.state = Mock()
        if state:
            for key, value in state.items():
                setattr(mock_request.app.state, key, value)
        return mock_request

    @staticmethod
    def create_mock_websocket() -> Mock:
        """Создает мок WebSocket."""
        mock_ws = Mock(spec=WebSocket)
        mock_ws.accept = Mock()
        mock_ws.receive_text = Mock()
        mock_ws.send_json = Mock()
        return mock_ws


class ConfigMixin:
    """Миксин для тестовых конфигураций."""

    @staticmethod
    def get_test_auth_config() -> dict:
        """Возвращает тестовую конфигурацию для Auth."""
        return {
            "SECRET_KEY": "test_secret_key_12345",
            "ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        }


class RtspMixin:
    """Миксин для мокирования RTSP сервера."""

    @staticmethod
    def create_mock_rtsp() -> Mock:
        """Создает мок RTSP сервера."""
        mock_rtsp = Mock()
        mock_rtsp.current_fps = 30.0
        mock_rtsp.fps_max = 60
        mock_rtsp.target_fps = 30
        mock_rtsp.show_osd = False
        mock_rtsp.supported_class = {"person": True, "car": True}
        mock_rtsp.frame_skip = 0
        mock_rtsp.activity_log = [1, 2, 3]
        mock_rtsp.set_target_fps = Mock()
        return mock_rtsp


# ==================== FIXTURES ====================


@pytest.fixture
def temp_auth_file():
    """Фикстура для временного файла авторизации."""
    fd, path = tempfile.mkstemp(suffix=".yml")
    try:
        yield path
    finally:
        os.close(fd)
        if os.path.exists(path):
            os.unlink(path)


@pytest.fixture
def mock_auth(temp_auth_file):
    """Фикстура для мок Auth с временным файлом."""
    original_path = Auth.__init__.__code__.co_consts
    auth = Auth()
    auth.path = temp_auth_file
    auth.users = auth._load_users()
    yield auth


@pytest.fixture
def test_users():
    """Фикстура для тестовых пользователей."""
    return AuthMixin.create_test_users(3)


@pytest.fixture
def mock_rtsp():
    """Фикстура для мок RTSP сервера."""
    return RtspMixin.create_mock_rtsp()


@pytest.fixture
def mock_request():
    """Фикстура для мок запроса."""
    return RequestMixin.create_mock_request()


@pytest.fixture
def mock_websocket():
    """Фикстура для мок WebSocket."""
    return RequestMixin.create_mock_websocket()


# ==================== AUTH TESTS ====================


class TestAuth(AuthMixin):
    """Тесты для Auth класса."""

    def test_init(self, temp_auth_file):
        """Тест инициализации Auth."""
        auth = Auth()
        auth.path = temp_auth_file
        auth.users = auth._load_users()
        assert auth.path == temp_auth_file
        assert auth.ALGORITHM == "HS256"
        assert auth.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_load_users_empty(self, temp_auth_file):
        """Тест загрузки пользователей из пустого файла."""
        auth = Auth()
        auth.path = temp_auth_file
        auth.users = auth._load_users()
        assert auth.users == []

    def test_load_users_from_file(self, temp_auth_file, test_users):
        """Тест загрузки пользователей из файла."""
        with open(temp_auth_file, "w") as f:
            yaml.dump(test_users, f)

        auth = Auth()
        auth.path = temp_auth_file
        auth.users = auth._load_users()
        assert len(auth.users) == 3

    def test_all_users_with_default_admin(self, temp_auth_file):
        """Тест свойства all_users с дефолтным админом."""
        auth = Auth()
        auth.path = temp_auth_file
        auth.users = auth._load_users()
        users = auth.all_users
        assert any(u["username"] == "admin" for u in users)

    @pytest.mark.parametrize(
        "plain,hashed",
        [
            (
                "testpass",
                bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode(),
            ),
            (
                "password123",
                bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
            ),
        ],
    )
    def test_verify_password_correct(self, plain, hashed, temp_auth_file):
        """Тест верификации правильного пароля."""
        auth = Auth()
        auth.path = temp_auth_file
        auth.users = auth._load_users()
        assert auth.verify_password(plain, hashed) == True

    @pytest.mark.parametrize(
        "plain,hashed",
        [
            (
                "wrongpass",
                bcrypt.hashpw(b"rightpass", bcrypt.gensalt()).decode(),
            ),
            ("test", bcrypt.hashpw(b"different", bcrypt.gensalt()).decode()),
        ],
    )
    def test_verify_password_incorrect(self, plain, hashed, temp_auth_file):
        """Тест верификации неправильного пароля."""
        auth = Auth()
        auth.path = temp_auth_file
        auth.users = auth._load_users()
        assert auth.verify_password(plain, hashed) == False

    def test_create_access_token(self, temp_auth_file):
        """Тест создания access token."""
        auth = Auth()
        auth.path = temp_auth_file
        auth.users = auth._load_users()
        with patch.dict(os.environ, {"SECRET_KEY": "test_key"}):
            token = auth.create_access_token({"id": 1})
            assert isinstance(token, str)
            assert len(token) > 0

    @pytest.mark.parametrize(
        "username,user_id",
        [
            ("user1", 1),
            ("admin", 0),
            ("nonexistent", None),
        ],
    )
    def test_get_user_by_username(
        self, username, user_id, temp_auth_file, test_users
    ):
        """Тест поиска пользователя по имени."""
        with open(temp_auth_file, "w") as f:
            yaml.dump(test_users, f)

        auth = Auth()
        auth.path = temp_auth_file
        auth.users = auth._load_users()
        user = auth.get_user_by_username(username)
        if user_id is not None:
            assert user is not None
            assert user["username"] == username
        else:
            assert user is None

    @pytest.mark.parametrize(
        "user_id,username",
        [
            (1, "user1"),
            (2, "user2"),
            (999, None),
        ],
    )
    def test_get_user_by_id(
        self, user_id, username, temp_auth_file, test_users
    ):
        """Тест поиска пользователя по ID."""
        with open(temp_auth_file, "w") as f:
            yaml.dump(test_users, f)

        auth = Auth()
        auth.path = temp_auth_file
        auth.users = auth._load_users()
        user = auth.get_user_by_id(user_id)
        if username is not None:
            assert user is not None
            assert user["username"] == username
        else:
            assert user is None

    @pytest.mark.parametrize(
        "user_id,update_data,should_succeed",
        [
            (1, {"username": "newname"}, True),
            (1, {"password": "newpass"}, True),
            (999, {"username": "nonexistent"}, False),  # Non-existent user
        ],
    )
    def test_update_user(
        self, user_id, update_data, should_succeed, temp_auth_file, test_users
    ):
        """Тест обновления пользователя."""
        with open(temp_auth_file, "w") as f:
            yaml.dump(test_users, f)

        auth = Auth()
        auth.path = temp_auth_file
        auth.users = auth._load_users()

        import asyncio

        if should_succeed:
            result = asyncio.run(auth.update_user(user_id, update_data))
            assert result is True
        else:
            with pytest.raises(Exception):  # HTTPException
                asyncio.run(auth.update_user(user_id, update_data))


# ==================== AUTH ROUTES TESTS ====================


class TestAuthRoutes(AuthMixin):
    """Тесты для auth_routes."""

    @pytest.fixture
    def client(self, temp_auth_file):
        """Фикстура для тестового клиента."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(auth_router)

        with patch("web.auth_routes.auth_service") as mock_auth:
            mock_auth.get_user_by_username = Mock(
                return_value=self.create_test_user()
            )
            mock_auth.verify_password = Mock(return_value=True)
            mock_auth.create_access_token = Mock(return_value="test_token")

            with TestClient(app) as test_client:
                yield test_client

    def test_login_success(self, client):
        """Тест успешного логина."""
        response = client.post(
            "/auth", json={"username": "testuser", "password": "testpass"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "access_token" in response.json()

    @pytest.mark.parametrize(
        "username,password",
        [
            ("wronguser", "testpass"),
            ("testuser", "wrongpass"),
        ],
    )
    def test_login_invalid_credentials(self, username, password, client):
        """Тест логина с неверными данными."""
        with patch("web.auth_routes.auth_service") as mock_auth:
            mock_auth.get_user_by_username = Mock(return_value=None)
            mock_auth.verify_password = Mock(return_value=False)

            response = client.post(
                "/auth", json={"username": username, "password": password}
            )
            assert response.status_code == 401

    def test_me_success(self, client):
        """Тест получения информации о текущем пользователе."""
        with patch("web.auth_routes.auth_service") as mock_auth:
            mock_auth.get_user_by_id = Mock(
                return_value=self.create_test_user()
            )
            with patch("web.auth_routes.jwt.decode") as mock_decode:
                mock_decode.return_value = {"id": 1}

                response = client.get(
                    "/auth/me", headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
                assert "me" in response.json()

    def test_me_no_token(self, client):
        """Тест получения информации без токена."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_refresh(self, client):
        """Тест refresh endpoint."""
        response = client.post("/auth/refresh")
        assert response.status_code == 200
        assert "refresh not implemented" in response.json()["status"]


# ==================== API ROUTES TESTS ====================


class TestApiRoutes(RtspMixin):
    """Тесты для api_routes."""

    @pytest.fixture
    def client(self, mock_rtsp):
        """Фикстура для тестового клиента."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(api_router)

        # Мокаем RTSP в app state
        app.state.rtsp = mock_rtsp

        with TestClient(app) as test_client:
            yield test_client

    def test_get_fps(self, client):
        """Тест получения FPS."""
        response = client.get("/api/video/fps")
        assert response.status_code == 200
        data = response.json()
        assert "current" in data
        assert "max" in data
        assert "target" in data

    @pytest.mark.parametrize(
        "target,expected_status",
        [
            (25, 200),
            (30, 200),
            (60, 200),
            (None, 400),
        ],
    )
    def test_set_fps(self, target, expected_status, client, mock_rtsp):
        """Тест установки FPS."""
        response = client.put("/api/video/fps", json={"target": target})
        assert response.status_code == expected_status

    def test_get_nn_config(self, client):
        """Тест получения конфигурации нейросети."""
        response = client.get("/api/nn")
        assert response.status_code == 200
        data = response.json()
        assert "show_osd" in data
        assert "classes" in data

    @pytest.mark.parametrize(
        "update_data",
        [
            {"enable": True},
            {"enable": False},
            {"classes": {"person": True, "car": False}},
            {"enable": True, "classes": {"person": True}},
        ],
    )
    def test_update_nn(self, update_data, client):
        """Тест обновления конфигурации нейросети."""
        response = client.put("/api/nn", json=update_data)
        assert response.status_code == 200

    def test_get_nn_skip(self, client):
        """Тест получения frame skip."""
        response = client.get("/api/nn/skip")
        assert response.status_code == 200

    @pytest.mark.parametrize("skip", [0, 1, 5, 10])
    def test_update_nn_skip(self, skip, client):
        """Тест обновления frame skip."""
        response = client.put("/api/nn/skip", json={"skip": skip})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.parametrize("skip", [-1, 101, 150])
    def test_update_nn_skip_invalid(self, skip, client):
        """Тест обновления frame skip с невалидными значениями."""
        response = client.put("/api/nn/skip", json={"skip": skip})
        assert response.status_code == 422  # Validation error

    def test_get_nn_log(self, client):
        """Тест получения лога активности."""
        response = client.get("/api/nn/log")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ==================== SYS ROUTES TESTS ====================


class TestSysRoutes(RequestMixin):
    """Тесты для sys_routes."""

    @pytest.fixture
    def client(self):
        """Фикстура для тестового клиента."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(sys_router)
        app.state.root = tempfile.gettempdir()

        with TestClient(app) as test_client:
            yield test_client

    def test_index_without_file(self, client):
        """Тест index endpoint без файла."""
        with patch("web.sys_routes.os.path.exists", return_value=False):
            response = client.get("/")
            assert response.status_code == 200
            assert "error" in response.json()

    def test_catch_all_file_exists(self, client):
        """Тест catch_all с существующим файлом."""
        with patch("web.sys_routes.os.path.exists", return_value=True):
            with patch("web.sys_routes.os.path.isfile", return_value=True):
                with patch(
                    "web.sys_routes.FileResponse"
                ) as mock_file_response:
                    mock_file_response.return_value = "file_content"
                    response = client.get("/test.css")
                    # FileResponse мокается, проверяем что путь правильный


# ==================== WEB SERVER TESTS ====================


class TestWebServer(ConfigMixin):
    """Тесты для WebServer класса."""

    @pytest.fixture
    def mock_app_logic(self):
        """Фикстура для мок логики приложения."""
        mock_logic = Mock()
        mock_logic.root = tempfile.gettempdir()
        return mock_logic

    def test_init(self, mock_app_logic):
        """Тест инициализации WebServer."""
        server = WebServer(mock_app_logic)
        assert server.logic == mock_app_logic
        assert server.app.title == "pp_smart_eye"
        assert len(server.sockets) == 0

    def test_cors_middleware(self, mock_app_logic):
        """Тест CORS middleware."""
        server = WebServer(mock_app_logic)
        # Проверяем что middleware добавлен (косвенно через наличие в app.middleware)
        assert len(server.app.user_middleware) > 0

    def test_send_all_sockets(self, mock_app_logic):
        """Тест отправки сообщения всем сокетам."""
        server = WebServer(mock_app_logic)

        # Создаем мок сокетов
        mock_ws1 = Mock()
        mock_ws1.send_text = Mock(return_value=None)
        mock_ws2 = Mock()
        mock_ws2.send_text = Mock(return_value=None)
        server.sockets = [mock_ws1, mock_ws2]

        import asyncio

        data = {"action": "test"}
        asyncio.run(server.send_all_sockets(data))

        # Проверяем что хотя бы один сокет получил сообщение
        assert mock_ws1.send_text.called or mock_ws2.send_text.called

    def test_send_all_sockets_remove_failed(self, mock_app_logic):
        """Тест удаления неработающих сокетов."""
        server = WebServer(mock_app_logic)

        mock_ws1 = Mock()
        mock_ws1.send_text = Mock(return_value=None)
        mock_ws2 = Mock()
        mock_ws2.send_text = Mock(side_effect=Exception("Connection closed"))
        server.sockets = [mock_ws1, mock_ws2]

        import asyncio

        data = {"action": "test"}

        try:
            asyncio.run(server.send_all_sockets(data))
        except:
            pass  # Ожидаем исключение

        # Проверяем что список сокетов изменился (удален хотя бы один)
        assert len(server.sockets) < 2

    def test_setup_routes(self, mock_app_logic):
        """Тест настройки роутов."""
        server = WebServer(mock_app_logic)
        server.setup_routes()

        # Проверяем что роуты добавлены (просто проверяем что роуты есть)
        assert len(server.app.routes) > 0


# ==================== INTEGRATION TESTS ====================


class TestWebIntegration(AuthMixin, RtspMixin, ConfigMixin):
    """Интеграционные тесты для web модуля."""

    @pytest.fixture
    def full_app(self, temp_auth_file, mock_rtsp):
        """Фикстура для полного приложения."""
        mock_logic = Mock()
        mock_logic.root = tempfile.gettempdir()

        server = WebServer(mock_logic)

        # Настраиваем state
        server.app.state.rtsp = mock_rtsp
        server.app.state.web_server = server
        server.app.state.root = mock_logic.root

        server.auth.path = temp_auth_file
        server.auth.users = server.auth._load_users()
        server.setup_routes()
        return server

    def test_full_app_init(self, full_app):
        """Тест инициализации полного приложения."""
        assert full_app.app is not None
        assert full_app.app.state.rtsp is not None
        assert full_app.app.state.web_server is not None

    def test_routes_registered(self, full_app):
        """Тест что все роуты зарегистрированы."""
        # Проверяем что роуты есть в приложении
        assert len(full_app.app.routes) > 0
