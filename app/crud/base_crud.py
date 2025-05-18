from typing import Generic, TypeVar, Type, List, Optional, Dict, Any, Tuple
from beanie import Document
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=Document)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
FilterSchemaType = TypeVar("FilterSchemaType", bound=BaseModel)

class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType, FilterSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD基类，提供默认的数据库操作
        """
        self.model = model

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        创建对象
        """
        obj_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**obj_data)
        await db_obj.insert()
        return db_obj

    async def get(self, id: str) -> Optional[ModelType]:
        """
        通过ID获取对象
        """
        return await self.model.get(id)

    async def update(self, id: str, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """
        更新对象
        """
        update_data = {
            k: v for k, v in obj_in.model_dump(exclude_unset=True).items()
            if v is not None
        }
        
        if not update_data:
            return await self.get(id)
            
        db_obj = await self.get(id)
        if db_obj:
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            await db_obj.save()
        
        return db_obj

    async def delete(self, id: str) -> bool:
        """
        删除对象
        """
        db_obj = await self.get(id)
        if db_obj:
            await db_obj.delete()
            return True
        return False

    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        sort_by: str = "updated_at",
        sort_desc: bool = True
    ) -> List[ModelType]:
        """
        获取多个对象
        """
        sort_direction = -1 if sort_desc else 1
        return await self.model.find().sort(
            [(sort_by, sort_direction)]
        ).skip(skip).limit(limit).to_list()

    async def count(self, query: Dict = None) -> int:
        """
        计数
        """
        if query is None:
            query = {}
        return await self.model.find(query).count()