from app.features.system_config.system_config_service import system_config_service
from app.schemas.system_config_schema import SystemConfigCreate, SystemConfigUpdate
from typing import Dict, Any, List

class SystemConfigController:
    def __init__(self):
        self.service = system_config_service
    
    async def get_configs(self, keys: List[str]) -> Dict[str, Any]:
        data = await self.service.get_configs(keys)
        return data
    
    async def set_config(self, config_data: SystemConfigCreate) -> Dict[str, Any]:
        data = await self.service.set_config(config_data)
        return {
            data.key: data.value
        }
    
    async def update_config(self, key: str, config_data: SystemConfigUpdate) -> Dict[str, Any]:
        data = await self.service.update_config(key, config_data)
        return {
            data.key: data.value
        }
    
    async def delete_config(self, key: str) -> bool:
        await self.service.delete_config(key)
        return True

# 全局Controller实例
system_config_controller = SystemConfigController()