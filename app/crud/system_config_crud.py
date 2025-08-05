from typing import List, Optional, Dict, Any
from datetime import datetime
from app.entities.system_config_entity import SystemConfig
from app.crud.base_crud import BaseCRUD
from app.schemas.system_config_schema import SystemConfigCreate, SystemConfigUpdate

class SystemConfigCRUD(BaseCRUD[SystemConfig, SystemConfigCreate, SystemConfigUpdate]):
    def __init__(self):
        super().__init__(SystemConfig)

    async def get_by_key(self, key: str) -> SystemConfig:
        return await SystemConfig.find_one({"key": key})

    async def get_by_keys(self, keys: List[str]) -> List[SystemConfig]:
        configs = await SystemConfig.find({"key": {"$in": keys}}).to_list()
        return configs

    async def get_public_configs(self) -> Dict[str, Any]:
        """获取所有公开配置"""
        configs = await SystemConfig.find({"is_public": True}).to_list()
        return {config.key: config.value for config in configs}
    
system_config_crud = SystemConfigCRUD()