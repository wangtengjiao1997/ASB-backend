import boto3
from typing import Optional
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.core.config import settings
from app.utils.logger_service import logger


class SMSService:
    """简洁的AWS SNS短信服务"""
    
    _instance = None
    _sns_client = None
    _sender_id = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
            cls._initialize()
        return cls._instance
    
    @classmethod
    def _initialize(cls):
        """初始化SNS客户端"""
        try:
            cls._sns_client = boto3.client(
                'sns',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
            cls._sender_id = getattr(settings, 'SMS_SENDER_ID', settings.PROJECT_NAME)
            
            logger.info(f"短信服务初始化成功，发送者ID: {cls._sender_id}")
            
        except Exception as e:
            logger.error(f"短信服务初始化失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"短信服务初始化失败: {str(e)}"
            )
    
    @classmethod
    async def send_sms(
        cls,
        phone_number: str,
        message: str,
        sender_id: Optional[str] = None,
        sms_type: str = "Transactional"
    ) -> bool:
        """
        发送短信
        
        Args:
            phone_number: 目标电话号码（国际格式，如 +8613800138000）
            message: 短信内容
            sender_id: 发送者ID（可选，默认使用配置中的）
            sms_type: 短信类型（Transactional 或 Promotional）
            
        Returns:
            bool: 发送是否成功
        """
        # 确保已初始化
        if cls._sns_client is None:
            cls.get_instance()
        
        try:
            # 准备消息属性
            message_attributes = {
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': sms_type
                }
            }
            
            # 使用提供的sender_id或默认的
            actual_sender_id = sender_id or cls._sender_id
            if actual_sender_id:
                message_attributes['AWS.SNS.SMS.SenderID'] = {
                    'DataType': 'String',
                    'StringValue': actual_sender_id
                }
            
            # 发送短信
            response = cls._sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes=message_attributes
            )
            
            message_id = response['MessageId']
            logger.info(f"短信发送成功: {message_id} -> {phone_number}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"短信发送失败 [{error_code}]: {error_message}")
            
            # 处理常见错误
            if error_code == 'InvalidParameter':
                raise HTTPException(
                    status_code=400,
                    detail=f"参数无效: {error_message}"
                )
            elif error_code == 'Throttling':
                logger.warning(f"短信发送被限流 [{error_code}]: {error_message}")
                return False
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"短信发送失败: {error_message}"
                )
                
        except Exception as e:
            logger.error(f"短信发送异常: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"短信发送失败: {str(e)}"
            )

   