import os
from datetime import datetime, timedelta
from typing import Dict, List

import bcrypt
import yaml
from fastapi import HTTPException
from jose import jwt


class Auth:
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    def __init__(self) -> None:
        self.path = "auth.yml"
        self.users = self._load_users()

    def _load_users(self) -> List[Dict]:
        if not os.path.exists(self.path):
            return []
        with open(self.path) as f:
            return yaml.load(f, Loader=yaml.FullLoader) or []

    @property
    def all_users(self) -> List[Dict]:
        users = list(self.users)
        # Дефолтный админ
        if not any(u["username"] == "admin" for u in users):
            users.append({"id": 0, "username": "admin", "password": "$2b$12$T/9VLLmm7TAkIYlhXdZwiemjx9W7JQrlfmZ41C/5Qu5Qj5X.KUDa2"})
        return users

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def get_user_by_username(self, username: str):
        return next((u for u in self.all_users if u["username"] == username), None)

    def get_user_by_id(self, user_id: int):
        return next((u for u in self.all_users if u["id"] == user_id), None)

    def __create_hash_psw(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    async def update_user(self, user_id: int, data: dict):
        if user_id == 666:
            return
        user = next((u for u in self.users if u["id"] == user_id), None)
        if not user:
            raise HTTPException(status_code=404)

        if "username" in data:
            user["username"] = data["username"]
        if "password" in data:
            user["password"] = self.__create_hash_psw(data["password"])

        with open(self.path, "w") as f:
            yaml.dump(self.users, f)
        return True
