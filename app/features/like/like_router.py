from fastapi import APIRouter, Depends
from app.features.like.like_controller import like_controller
from app.entities.user_entity import User
from app.middleware.auth_middleware import get_current_user_required
from app.schemas.like_schema import LikeClick
from app.schemas.response_schema import BaseResponse

router = APIRouter(prefix="/likes", tags=["likes"])

@router.post("/like_click")
async def like_click(
    like_click: LikeClick,
    user: User = Depends(get_current_user_required)
):
    data = await like_controller.like_click(like_click, user)
    return BaseResponse.success(data)
