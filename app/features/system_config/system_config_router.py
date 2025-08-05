from fastapi import APIRouter, Query
from app.features.system_config.system_config_controller import system_config_controller
from app.schemas.system_config_schema import SystemConfigCreate, SystemConfigUpdate
from app.schemas.response_schema import BaseResponse
from typing import Dict, Any, List

router = APIRouter(prefix="/system_config", tags=["系统配置"])

@router.get("/get", response_model=BaseResponse[Dict[str, Any]])
async def get_configs(keys: List[str] = Query(...)):
    data = await system_config_controller.get_configs(keys)
    return BaseResponse.success(data=data)

@router.post("/set", response_model=BaseResponse[Dict[str, Any]])  
async def set_config(config_data: SystemConfigCreate):
    data = await system_config_controller.set_config(config_data)
    return BaseResponse.success(data=data)

@router.put("/update/{key}", response_model=BaseResponse[Dict[str, Any]])
async def update_config(key: str, config_data: SystemConfigUpdate):
    data = await system_config_controller.update_config(key, config_data)
    return BaseResponse.success(data=data)

@router.delete("/delete/{key}", response_model=BaseResponse[Dict[str, bool]])
async def delete_config(key: str):
    data = await system_config_controller.delete_config(key)
    return BaseResponse.success(data={"success": data})