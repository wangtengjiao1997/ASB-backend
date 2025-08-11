from app.crud.user_crud import user_crud
from app.crud.system_config_crud import system_config_crud

# 导出CRUD实例，方便直接导入
__all__ = ["user_crud", "system_config_crud"]