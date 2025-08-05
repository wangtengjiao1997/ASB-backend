from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from app.entities.report_entity import Report
from app.schemas.report_schema import ReportCreate, ReportFilter, ReportIncrementalParams, ReportUpdate
from app.crud.base_crud import BaseCRUD

class ReportCRUD(BaseCRUD[Report, ReportCreate, ReportUpdate]):
    def __init__(self):
        super().__init__(Report)
    
    async def _build_filter_query(self, filter_params: ReportFilter) -> Dict:
        """构建报告过滤查询条件"""
        query = {"is_deleted": False}
        
        if filter_params.type:
            query["type"] = filter_params.type
            
        if filter_params.post_id:
            query["params.post_id"] = filter_params.post_id
            
        if filter_params.agent_id:
            query["params.agent_id"] = filter_params.agent_id
            
                
        return query

    async def get_reports_incremental(
        self,
        filter_params: ReportFilter,
        incremental_params: ReportIncrementalParams
    ) -> Tuple[List[Report], bool, int]:
        """
        增量获取报告
        
        Args:
            filter_params: 报告过滤条件
            incremental_params: 增量参数
            
        Returns:
            Tuple[List[Report], bool, int]: 报告列表、是否还有更多、总数
        """
        query = await self._build_filter_query(filter_params)
        total = await Report.find(query).count()
        
        if incremental_params.direction == "before":  # before - 获取历史报告
            if incremental_params.last_id:
                last_report = await Report.find_one({"_id": incremental_params.last_id})
                if last_report:
                    query["created_at"] = {"$lt": last_report.created_at}           
        else:  # after - 获取新报告
            if incremental_params.last_id:
                last_report = await Report.find_one({"_id": incremental_params.last_id})
                if last_report:
                    query["created_at"] = {"$gt": last_report.created_at}
        
        sort_direction = -1  # 按创建时间倒序
        
        # 执行查询，多查一条用于判断是否还有更多
        reports = await Report.find(query).sort(
            [("created_at", sort_direction)]
        ).limit(incremental_params.limit + 1).to_list()
        
        # 判断是否还有更多
        has_more = len(reports) > incremental_params.limit
        if has_more:
            reports = reports[:-1]  # 移除多查的那一条
        
        return reports, has_more, total

# 创建单例实例
report_crud = ReportCRUD()