from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from app.features.report.report_controller import report_controller
from app.schemas.report_schema import ReportCreate, ReportResponse, ReportIncrementalResponse, ReportIncrementalParams, ReportFilter
from app.schemas.response_schema import BaseResponse

router = APIRouter(prefix="/report", tags=["报告管理"])
token_auth_scheme = HTTPBearer()

@router.post("/create", response_model=BaseResponse[ReportResponse])
async def create_report(report_data: ReportCreate):
    data = await report_controller.create_report(report_data)
    return BaseResponse.success(data=data)

@router.delete("/delete/{report_id}", response_model=BaseResponse[bool])
async def delete_report(report_id: str):
    data = await report_controller.delete_report(report_id)
    return BaseResponse.success(data=data)

@router.get("/report/{report_id}", response_model=BaseResponse[ReportResponse])
async def get_report(report_id: str):
    data = await report_controller.get_report(report_id)
    return BaseResponse.success(data=data)