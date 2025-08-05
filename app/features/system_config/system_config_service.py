from typing import Dict, Any, List, Optional
from app.crud.system_config_crud import system_config_crud
from app.entities.system_config_entity import SystemConfig
from app.schemas.system_config_schema import (
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigFilter
)

class SystemConfigService:
    def __init__(self):
        self.system_config_crud = system_config_crud

    async def get_configs(self, keys: List[str]) -> Dict[str, Any]:
        """获取配置值"""
        data = await self.system_config_crud.get_by_keys(keys)
        key_value_dict = {key: "" for key in keys}
        for config in data:
            key_value_dict[config.key] = config.value
        return key_value_dict

    async def set_config(
        self,
        config_data: SystemConfigCreate
    ) -> SystemConfig:
        """设置配置"""
        existing_config = await self.system_config_crud.get_by_key(config_data.key)
        if existing_config:
            data = await self.system_config_crud.update(
                str(existing_config.id), 
                SystemConfigUpdate.model_validate(config_data.model_dump())
            )
            return data
        else:
            data = await self.system_config_crud.create(config_data)
            return data

    async def update_config(
        self,
        key: str,
        config_data: SystemConfigUpdate
    ) -> Optional[SystemConfig]:
        """更新配置"""
        data = await self.system_config_crud.update(key, config_data)
        return data

    async def delete_config(self, key: str) -> bool:
        """删除配置"""
        await self.system_config_crud.delete(key)
        return True

# 全局服务实例
system_config_service = SystemConfigService()