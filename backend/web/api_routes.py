from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import BaseModel, Field

from .auth import Auth

router = APIRouter(prefix="/api")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
auth_service = Auth()


class SkipUpdateSchema(BaseModel):
    skip: int = Field(..., ge=0, le=100)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401)
        return auth_service.get_user_by_id(user_id)
    except:
        raise HTTPException(status_code=401)


def get_rtsp(request: Request):
    return request.app.state.rtsp


@router.get("/video/fps")
async def get_fps(rtsp=Depends(get_rtsp)):
    return {"current": rtsp.current_fps, "max": rtsp.fps_max, "target": rtsp.target_fps}


@router.put("/video/fps")
async def set_fps(data: dict, rtsp=Depends(get_rtsp)):
    target = data.get("target")
    if target is not None:
        rtsp.set_target_fps(target)
        return "OK"
    raise HTTPException(status_code=400)


@router.get("/nn")
async def get_nn_config(rtsp=Depends(get_rtsp)):
    return {"show_osd": rtsp.show_osd, "classes": rtsp.supported_class}


@router.put("/nn")
async def update_nn(data: dict, rtsp=Depends(get_rtsp)):
    if "enable" in data:
        rtsp.show_osd = data["enable"]
    if "classes" in data:
        rtsp.supported_class = data["classes"]
    return "OK"


@router.get("/nn/skip")
async def get_nn_skip(rtsp=Depends(get_rtsp)):
    if not rtsp:
        raise HTTPException(status_code=503, detail="RTSP server not ready")
    return rtsp.frame_skip


@router.put("/nn/skip")
async def update_nn_skip(data: SkipUpdateSchema, rtsp=Depends(get_rtsp)):
    if not rtsp:
        raise HTTPException(status_code=503, detail="RTSP server not ready")

    rtsp.frame_skip = data.skip
    return {"status": "success", "message": f"Frame skip updated to {data.skip}"}


@router.get("/nn/log")
async def get_nn_log(rtsp=Depends(get_rtsp)):
    if not rtsp:
        return []
    return rtsp.activity_log
