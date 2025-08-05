from fastapi import APIRouter, Depends
from app.features.subscribe.subscribe_controller import subscribe_controller
from app.entities.user_entity import User
from app.middleware.auth_middleware import get_current_user_required
from app.schemas.subscribe_schema import SubscribeClick
from app.schemas.response_schema import BaseResponse

router = APIRouter(prefix="/subscribes", tags=["subscribes"])

@router.post("/subscribe_click")
async def subscribe_click(
    subscribe_click: SubscribeClick,
    user: User = Depends(get_current_user_required)
):
    data = await subscribe_controller.subscribe_click(subscribe_click, user)
    return BaseResponse.success(data)
