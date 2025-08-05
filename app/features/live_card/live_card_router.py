from fastapi import APIRouter, Depends
from app.features.live_card.live_card_controller import live_card_controller
from app.schemas.live_card_schema import LiveCardCreate, LiveCardUpdate, LiveCardFilter, LiveCardIncrementalParams
from app.entities.user_entity import User
from app.middleware.auth_middleware import get_current_user_required, get_current_user_optional
from typing import Optional

router = APIRouter(prefix="/live_cards", tags=["live_cards"])

@router.post("/create")
async def create_live_card(
    data: LiveCardCreate,
    user: User = Depends(get_current_user_required)
):
    return await live_card_controller.create_live_card(data)

@router.put("/update/{live_card_id}")
async def update_live_card(
    live_card_id: str,
    data: LiveCardUpdate,
    user: User = Depends(get_current_user_required)
):
    return await live_card_controller.update_live_card(live_card_id, data)

@router.get("/explore")
async def get_explore_live_cards(
    filter_params: LiveCardFilter = Depends(),
    incremental_params: LiveCardIncrementalParams = Depends(),
    user: Optional[User] = Depends(get_current_user_optional)
):
    return await live_card_controller.get_explore_live_cards(filter_params, incremental_params, user)

@router.get("/subscribing")
async def get_subscribing_live_cards(
    filter_params: LiveCardFilter = Depends(),
    incremental_params: LiveCardIncrementalParams = Depends(),
    user: Optional[User] = Depends(get_current_user_optional)
):
    return await live_card_controller.get_subscribing_live_cards(filter_params, incremental_params, user)

@router.post("/add_share_count/{live_card_id}")
async def add_share_count(live_card_id: str):
    return await live_card_controller.add_share_count(live_card_id)