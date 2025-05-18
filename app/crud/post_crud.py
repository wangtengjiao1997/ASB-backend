from typing import List, Optional, Dict, Any, Tuple
from app.entities.post_entity import Post
from app.schemas.post_shema import PostCreate, PostUpdate, PostFilter, PaginationParams
from app.crud.base_crud import BaseCRUD

class PostCRUD(BaseCRUD[Post, PostCreate, PostUpdate, PostFilter]):
    def __init__(self):
        super().__init__(Post)
    
    async def _build_filter_query(self, filter_params: PostFilter) -> Dict:
        """构建帖子过滤查询条件"""
        query = {}
        
        if filter_params.agentId:
            query["agentId"] = filter_params.agentId
            
        if filter_params.tag:
            query["tag"] = {"$in": filter_params.tag}
            
        if filter_params.cardType:
            query["cardType"] = filter_params.cardType
            
        if filter_params.status:
            query["status"] = filter_params.status
            
        if filter_params.start_date:
            query["dateTime"] = {"$gte": filter_params.start_date}
            
        if filter_params.end_date:
            if "dateTime" in query:
                query["dateTime"]["$lte"] = filter_params.end_date
            else:
                query["dateTime"] = {"$lte": filter_params.end_date}
                
        if filter_params.published is not None:
            query["published"] = filter_params.published
            
        if filter_params.visibility:
            query["visibility"] = filter_params.visibility.value
                
        return query
    
    async def get_posts_with_filter(
        self,
        filter_params: PostFilter,
        pagination: PaginationParams
    ) -> Tuple[List[Post], int]:
        """带分页和过滤的帖子列表查询"""
        query = await self._build_filter_query(filter_params)
        
        # 构建排序
        sort_direction = -1 if pagination.sort_desc else 1
        sort_field = pagination.sort_by
        
        # 计算总数
        total = await Post.find(query).count()
        
        # 计算偏移量
        skip = (pagination.page - 1) * pagination.page_size
        
        # 查询带分页的结果
        posts = await Post.find(query).sort(
            [(sort_field, sort_direction)]
        ).skip(skip).limit(pagination.page_size).to_list()
        
        return posts, total

# 创建单例实例
post_crud = PostCRUD() 