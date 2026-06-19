import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, Response
from jose import jwt
from pydantic import BaseModel

from .auth import Auth

router = APIRouter(prefix="/auth")
auth_service = Auth()


class LoginSchema(BaseModel):
    username: str
    password: str


@router.post("")
async def login(data: LoginSchema, response: Response) -> Dict[str, Any]:
    user = auth_service.get_user_by_username(data.username)

    if not user or not auth_service.verify_password(
        data.password, user["password"]
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth_service.create_access_token(data={"id": user["id"]})

    response.headers["Authorization"] = f"Bearer {token}"

    return {
        "status": "success",
        "access_token": token,
    }  # Ключ из вашего tokenDefaultKey


@router.get("/me")
async def me(request: Request) -> Dict[str, Any]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401)

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY", ""),
            algorithms=[auth_service.ALGORITHM],
        )
        user_id = payload.get("id", "")
        user = auth_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=401)

        return {
            "me": {
                "id": str(user["id"]),
                "username": user["username"],
                "role": "admin",
            }
        }
    except Exception:
        raise HTTPException(status_code=401)


@router.post("/refresh")
async def refresh() -> Dict[str, str]:
    return {"status": "refresh not implemented"}
