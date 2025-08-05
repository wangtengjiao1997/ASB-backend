from app.crud import report_crud
from app.schemas.report_schema import ReportCreate, ReportUpdate, ReportFilter, ReportIncrementalParams
from app.entities.report_entity import Report
from typing import List, Tuple, Optional

class ReportService:
    def __init__(self):
        self.report_crud = report_crud
    
    async def create_report(self, data: ReportCreate) -> Report:
        """创建举报"""
        return await self.report_crud.create(data)
    
    async def get_report(self, report_id: str) -> Optional[Report]:
        """根据ID获取举报"""
        return await self.report_crud.get(report_id)
    
    async def update_report(self, report_id: str, data: ReportUpdate) -> Report:
        """更新举报"""
        report = await self.report_crud.get(report_id)
        if not report:
            raise ValueError("举报不存在")
        
        return await self.report_crud.update(report_id, data)
    
    async def delete_report(self, report_id: str) -> bool:
        """删除举报"""
        return await self.report_crud.delete(report_id)
    
    async def get_reports_incremental(self, filter_params: ReportFilter, incremental_params: ReportIncrementalParams) -> Tuple[List[Report], bool, int]:
        """获取举报列表"""
        reports, has_more, total = await self.report_crud.get_reports_incremental(filter_params, incremental_params)
        return reports, has_more, total

# 全局服务实例
report_service = ReportService()