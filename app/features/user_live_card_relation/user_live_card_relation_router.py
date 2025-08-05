from fastapi import APIRouter, Depends
from app.features.user_live_card_relation.user_live_card_relation_controller import user_live_card_relation_controller
from app.middleware.auth_middleware import get_current_user_required, get_current_user_optional
from app.entities.user_entity import User

router = APIRouter(
    prefix="/user-live-card-relation",
    tags=["user-live-card-relation"]
)

@router.get("/last-read-time/{live_card_id}")
async def get_last_read_time(
    live_card_id: str,
    current_user: User = Depends(get_current_user_required)
):
    return await user_live_card_relation_controller.get_last_read_time(
        current_user=current_user,
        live_card_id=live_card_id
    )

@router.post("/last-read-time/{live_card_id}")
async def update_last_read_time(
    live_card_id: str,
    current_user: User = Depends(get_current_user_required)
):
    return await user_live_card_relation_controller.update_last_read_time(
        current_user=current_user,
        live_card_id=live_card_id
    )