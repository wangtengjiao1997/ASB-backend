from app.crud.user_crud import user_crud
from app.crud.post_crud import post_crud
from app.crud.user_feed_crud import user_feed_crud

# 导出CRUD实例，方便直接导入
__all__ = ["user_crud", "post_crud", "user_feed_crud"]