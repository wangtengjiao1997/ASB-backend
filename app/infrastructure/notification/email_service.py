import boto3
from typing import List, Optional, Union
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.core.config import settings
from app.utils.logger_service import logger


class EmailService:
    """简洁的AWS SES邮件服务"""
    
    _instance = None
    _ses_client = None
    _from_email = None
    _from_name = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
            cls._initialize()
        return cls._instance
    
    @classmethod
    def _initialize(cls):
        """初始化SES客户端"""
        try:
            cls._ses_client = boto3.client(
                'ses',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
            cls._from_email = settings.EMAIL_FROM
            cls._from_name = getattr(settings, 'EMAIL_FROM_NAME', settings.PROJECT_NAME)
            
            logger.info(f"邮件服务初始化成功，发件人: {cls._from_email}")
            
        except Exception as e:
            logger.error(f"邮件服务初始化失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"邮件服务初始化失败: {str(e)}"
            )
    
    @classmethod
    async def send_text_email(
        cls,
        to_email: Union[str, List[str]],
        subject: str,
        text_content: str
    ) -> bool:
        """
        发送纯文本邮件
        
        Args:
            to_email: 收件人邮箱（单个或列表）
            subject: 邮件主题
            text_content: 纯文本内容
            
        Returns:
            bool: 发送是否成功
        """
        # 确保已初始化
        if cls._ses_client is None:
            cls.get_instance()
        
        try:
            # 处理收件人
            if isinstance(to_email, str):
                to_emails = [to_email]
            else:
                to_emails = to_email
            
            # 发送邮件
            response = cls._ses_client.send_email(
                Source=f"{cls._from_name} <{cls._from_email}>",
                Destination={
                    'ToAddresses': to_emails
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_content,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            message_id = response['MessageId']
            logger.info(f"邮件发送成功: {message_id} -> {to_emails}")
            return True
            
        except ClientError as e:
            code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"邮件发送失败 [{code}]: {error_message}")
            
            # 处理常见错误
            if code == 'MessageRejected':
                raise HTTPException(
                    status_code=400,
                    detail=f"邮件被拒绝: {error_message}"
                )
            elif code == 'MailFromDomainNotVerified':
                logger.warning(f"邮件发送失败, 发件人域名未验证 [{code}]: {error_message}")
                return False
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"邮件发送失败: {error_message}"
                )
                
        except Exception as e:
            logger.error(f"邮件发送异常: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"邮件发送失败: {str(e)}"
            )

    @classmethod
    async def send_welcome_email(cls, user_email: str, user_name: str) -> bool:
        """发送欢迎邮件"""
        subject = f"欢迎加入{settings.PROJECT_NAME}"
        content = f"""
亲爱的 {user_name}，

欢迎加入{settings.PROJECT_NAME}！我们很高兴您的加入。

如果您有任何问题，请随时联系我们。

祝好，
{settings.PROJECT_NAME}团队
        """
        
        return await cls.send_text_email(
            to_email=user_email,
            subject=subject,
            text_content=content
        )

    @classmethod
    async def send_notification_email(
        cls, 
        user_email: str, 
        user_name: str, 
        title: str, 
        message: str
    ) -> bool:
        """发送通知邮件"""
        subject = title
        content = f"""
亲爱的 {user_name}，

{message}

祝好，
{settings.PROJECT_NAME}团队
        """
        
        return await cls.send_text_email(
            to_email=user_email,
            subject=subject,
            text_content=content
        )

    @classmethod
    async def send_password_reset_email(
        cls, 
        user_email: str, 
        user_name: str, 
        reset_token: str
    ) -> bool:
        """发送密码重置邮件"""
        subject = "重置密码"
        reset_link = f"https://yourapp.com/reset-password?token={reset_token}"
        content = f"""
亲爱的 {user_name}，

我们收到了您的密码重置请求。

重置链接: {reset_link}

此链接将在24小时后过期。

如果您没有请求重置密码，请忽略此邮件。

祝好，
{settings.PROJECT_NAME}团队
        """
        
        return await cls.send_text_email(
            to_email=user_email,
            subject=subject,
            text_content=content
        )