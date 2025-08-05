import json
import os
from typing import Dict, Any, Optional, List
from firebase_admin import credentials, messaging, initialize_app
import firebase_admin
from app.utils.logger_service import logger
from app.core.config import settings
from app.schemas.fcm_schema import FcmNotificationMessage

class FCMService:
    def __init__(self):
        self.app = None
        self.initialized = False
        
    async def initialize(self):
        """初始化Firebase Admin SDK"""
        if self.initialized:
            return
            
        try:
            # 检查是否已经初始化过
            if not firebase_admin._apps:
                # 使用服务账号JSON文件
                credentials_path = settings.FCM_CREDENTIALS_PATH
                if os.path.exists(credentials_path):
                    cred = credentials.Certificate(credentials_path)
                    self.app = initialize_app(cred)
                    logger.info("FCM初始化成功")
                else:
                    raise FileNotFoundError(f"FCM服务账号文件不存在: {credentials_path}")
            else:
                self.app = firebase_admin.get_app()
            
            self.initialized = True
            
        except Exception as e:
            logger.error(f"FCM初始化失败: {str(e)}")
            raise
    
    async def send_notification(
        self,
        message: FcmNotificationMessage
    ) -> Dict[str, Any]:
        """
        发送测试通知
        
        参数:
        - token: FCM设备token
        - title: 通知标题
        - body: 通知内容
        """
        await self.initialize()
        
        try:
            print("fcm token:", message.message.token)
            firebase_message = message.build_firebase_message()
            # 发送消息
            response = messaging.send(firebase_message)
            
            logger.info(f"FCM测试通知发送成功: message_id={response}")
            
            return {
                "success": True,
                "message_id": response,
                "message": "通知发送成功"
            }
            
        except messaging.UnregisteredError:
            logger.warning("FCM token已失效")
            return {
                "success": False,
                "error": "TOKEN_INVALID",
                "message": "设备token已失效"
            }
        except Exception as e:
            logger.error(f"FCM发送失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "通知发送失败"
            }

    async def send_batch_notification(
        self,
        tokens: List[str],
        title: str = "批量测试通知",
        body: str = "这是一条批量测试通知",
        batch_size: int = 500
    ) -> Dict[str, Any]:
        """
        批量发送测试通知
        
        参数:
        - tokens: FCM设备token列表
        - title: 通知标题
        - body: 通知内容
        - batch_size: 批次大小（FCM限制每批最多500个）
        """
        await self.initialize()
        
        if not tokens:
            return {
                "success": True,
                "total_tokens": 0,
                "success_count": 0,
                "failure_count": 0,
                "results": []
            }
        
        # 分批处理
        all_results = []
        success_count = 0
        failure_count = 0
        
        for i in range(0, len(tokens), batch_size):
            batch_tokens = tokens[i:i + batch_size]
            
            try:
                # 构建批量消息
                multicast_message = messaging.MulticastMessage(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    data={
                        "test": "true",
                        "batch": "true",
                        "timestamp": str(int(__import__('time').time()))
                    },
                    tokens=batch_tokens,
                    # iOS特定配置
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                alert=messaging.ApsAlert(
                                    title=title,
                                    body=body
                                ),
                                badge=1,
                                sound="default"
                            )
                        )
                    )
                )
                
                # 批量发送
                response = messaging.send_multicast(multicast_message)
                
                # 处理响应
                for j, result in enumerate(response.responses):
                    token = batch_tokens[j]
                    if result.success:
                        success_count += 1
                        all_results.append({
                            "success": True,
                            "token": token[:10] + "...",  # 只显示token前10位
                            "message_id": result.message_id
                        })
                    else:
                        failure_count += 1
                        error_code = result.exception.code if result.exception else "UNKNOWN"
                        all_results.append({
                            "success": False,
                            "token": token[:10] + "...",
                            "error": error_code,
                            "message": str(result.exception) if result.exception else "未知错误"
                        })
                
                logger.info(f"FCM批量发送完成: 批次大小={len(batch_tokens)}, 成功={response.success_count}, 失败={response.failure_count}")
                
            except Exception as e:
                logger.error(f"FCM批量发送异常: {str(e)}")
                # 记录整个批次失败
                for token in batch_tokens:
                    failure_count += 1
                    all_results.append({
                        "success": False,
                        "token": token[:10] + "...",
                        "error": "BATCH_ERROR",
                        "message": str(e)
                    })
        
        return {
            "success": True,
            "total_tokens": len(tokens),
            "success_count": success_count,
            "failure_count": failure_count,
            "results": all_results
        }

# 创建全局实例
fcm_service = FCMService()