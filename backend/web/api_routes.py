import os
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import BaseModel, Field

from rtsp_server.RtspMergeServer import RtspMergeServer

from .auth import Auth

router = APIRouter(prefix="/api")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
auth_service = Auth()


class SkipUpdateSchema(BaseModel):
    skip: int = Field(..., ge=0, le=100)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> Dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY", ""),
            algorithms=[auth_service.ALGORITHM],
        )
        user_id: int | None = payload.get("id", None)
        if user_id is None:
            raise HTTPException(status_code=401)
        return auth_service.get_user_by_id(user_id)
    except Exception as e:
        raise HTTPException(status_code=401)


def get_rtsp(request: Request) -> RtspMergeServer:
    return request.app.state.rtsp


@router.get("/video/fps")
async def get_fps(
    current_user: Dict[str, Any] = Depends(get_current_user),
    rtsp: RtspMergeServer = Depends(get_rtsp),
) -> Dict[str, Any]:
    return {
        "current": rtsp.current_fps,
        "max": rtsp.fps_max,
        "target": rtsp.target_fps,
    }


@router.put("/video/fps")
async def set_fps(
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    rtsp: RtspMergeServer = Depends(get_rtsp),
) -> str:
    target = data.get("target")
    if target is not None:
        rtsp.set_target_fps(target)
        return "OK"
    raise HTTPException(status_code=400)


@router.get("/nn")
async def get_nn_config(
    current_user: Dict[str, Any] = Depends(get_current_user),
    rtsp: RtspMergeServer = Depends(get_rtsp),
) -> Dict[str, Any]:
    return {"show_osd": rtsp.show_osd, "classes": rtsp.supported_class}


@router.put("/nn")
async def update_nn(
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    rtsp: RtspMergeServer = Depends(get_rtsp),
) -> str:
    if "enable" in data:
        rtsp.show_osd = data["enable"]
    if "classes" in data:
        rtsp.supported_class = data["classes"]
    return "OK"


@router.get("/nn/skip")
async def get_nn_skip(
    current_user: Dict[str, Any] = Depends(get_current_user),
    rtsp: RtspMergeServer = Depends(get_rtsp),
) -> int:
    if not rtsp:
        raise HTTPException(status_code=503, detail="RTSP server not ready")
    return rtsp.frame_skip


@router.put("/nn/skip")
async def update_nn_skip(
    data: SkipUpdateSchema,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rtsp: RtspMergeServer = Depends(get_rtsp),
) -> Dict[str, str]:
    if not rtsp:
        raise HTTPException(status_code=503, detail="RTSP server not ready")

    rtsp.frame_skip = data.skip
    return {
        "status": "success",
        "message": f"Frame skip updated to {data.skip}",
    }


@router.get("/nn/log")
async def get_nn_log(
    current_user: Dict[str, Any] = Depends(get_current_user),
    rtsp: RtspMergeServer = Depends(get_rtsp),
) -> list[int]:
    if not rtsp:
        return []
    return rtsp.activity_log
