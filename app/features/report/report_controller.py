from app.features.report.report_service import report_service
from app.crud import user_crud
from app.schemas.report_schema import ReportResponse, ReportCreate, ReportUpdate, ReportFilter, ReportIncrementalParams, ReportIncrementalResponse
from app.entities.user_entity import User
from typing import List, Optional
from datetime import datetime

class ReportController:
    def __init__(self):
        self.service = report_service
        self.user_crud = user_crud
    
    async def create_report(self, data: ReportCreate) -> ReportResponse:
        """创建举报并组装响应数据"""
        report = await self.service.create_report(data)

        return ReportResponse(
            **report.model_dump()
        )
    
    async def get_report(self, report_id: str) -> ReportResponse:
        """根据ID获取举报"""
        report = await self.service.get_report(report_id)
        if not report:
            raise ValueError("举报不存在")
        
        return ReportResponse(
            **report.model_dump()
        )
    
    async def update_report(self, report_id: str, data: ReportUpdate) -> ReportResponse:
        """更新举报"""
        report = await self.service.update_report(report_id, data)
        return ReportResponse(**report.model_dump())

    async def delete_report(self, report_id: str) -> bool:
        """删除举报"""
        return await self.service.delete_report(report_id)

# 全局Controller实例
report_controller = ReportController()