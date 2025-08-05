from pydantic import BaseModel, Field
from typing import Optional, List
from firebase_admin import messaging

# === FCM 推送通知相关模型 ===

# FCM 基础通知内容
class FcmNotification(BaseModel):
    title: str = Field(..., description="通知标题")
    body: str = Field(..., description="通知内容描述")

# FCM 数据载荷
class FcmData(BaseModel):
    route_path: Optional[str] = Field(None, description="路由路径")

# Android 特定通知配置
class AndroidNotification(BaseModel):
    title: str = Field(..., description="Android通知标题")
    body: str = Field(..., description="Android通知内容")
    image: Optional[str] = Field(None, description="通知图片URL")
    channel_id: str = Field(default="default_channel", description="通知渠道ID")
    priority: str = Field(default="high", description="通知优先级")
    default_sound: bool = Field(default=True, description="使用默认声音")
    default_vibrate_timings: bool = Field(default=True, description="使用默认震动")

class AndroidConfig(BaseModel):
    notification: AndroidNotification

# iOS APNs 通知配置
class ApsAlert(BaseModel):
    title: str = Field(..., description="iOS通知标题")
    subtitle: Optional[str] = Field(None, description="iOS通知副标题")
    body: str = Field(..., description="iOS通知内容")

class ApsPayload(BaseModel):
    alert: ApsAlert
    mutable_content: int = Field(default=1, description="可变内容", alias="mutable-content")
    sound: str = Field(default="default", description="通知声音")

class ApnsPayload(BaseModel):
    aps: ApsPayload
    image_url: Optional[str] = Field(None, description="图片URL")

class ApnsConfig(BaseModel):
    payload: ApnsPayload

# FCM 消息主体
class FcmMessage(BaseModel):
    token: str = Field(..., description="用户FCM令牌")
    notification: FcmNotification = Field(..., description="通知内容")
    data: Optional[FcmData] = Field(None, description="自定义数据")
    android: Optional[AndroidConfig] = Field(None, description="Android特定配置")
    apns: Optional[ApnsConfig] = Field(None, description="iOS特定配置")

# FCM 通知消息完整结构
class FcmNotificationMessage(BaseModel):
    message: FcmMessage = Field(..., description="FCM消息")

    class Config:
        # 支持字段别名
        validate_by_name = True
        
    def build_firebase_message(self):
        """
        将 FcmNotificationMessage 转换为 Firebase messaging.Message
        
        返回:
        - Firebase messaging.Message 对象
        """
        msg = self.message
        
        # 构建基础数据载荷
        data_payload = {}
        if msg.data:
            if msg.data.route_path:
                data_payload["route_path"] = msg.data.route_path
        
        # 构建 Android 配置
        android_config = None
        if msg.android:
            android_config = messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    title=msg.android.notification.title,
                    body=msg.android.notification.body,
                    image=msg.android.notification.image,
                    channel_id=msg.android.notification.channel_id,
                    priority=msg.android.notification.priority,
                    default_sound=msg.android.notification.default_sound,
                    default_vibrate_timings=msg.android.notification.default_vibrate_timings
                )
            )
        
        # 构建 APNS 配置
        apns_config = None
        if msg.apns:
            fcm_options = None
            if msg.apns.payload.image_url:
                fcm_options = messaging.APNSFCMOptions(
                    image=msg.apns.payload.image_url
                )
            
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=msg.apns.payload.aps.alert.title,
                            subtitle=msg.apns.payload.aps.alert.subtitle,
                            body=msg.apns.payload.aps.alert.body
                        ),
                        mutable_content=msg.apns.payload.aps.mutable_content,
                        sound=msg.apns.payload.aps.sound
                    )
                ),
                fcm_options=fcm_options
            )

        # 构建最终的 Firebase Message
        return messaging.Message(
            token=msg.token,
            notification=messaging.Notification(
                title=msg.notification.title,
                body=msg.notification.body
            ),
            data=data_payload if data_payload else None,
            android=android_config,
            apns=apns_config
        )
    
    @classmethod
    def create_simple_notification(
        cls,
        token: str,
        title: str,
        subtitle: str,
        body: str,
        route_path: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> "FcmNotificationMessage":
        """
        创建简单的FCM通知消息
        
        Args:
            token: FCM令牌
            title: 通知标题
            body: 通知内容
            route_path: 路由路径
            image_url: 图片URL
            
        Returns:
            FcmNotificationMessage实例
        """
        data = FcmData(route_path=route_path) if route_path else None
        
        android_config = AndroidConfig(
            notification=AndroidNotification(
                title=title,
                body=body,
                image=image_url
            )
        ) if image_url else AndroidConfig(
            notification=AndroidNotification(title=title, body=body)
        )
        
        apns_config = ApnsConfig(
            payload=ApnsPayload(
                aps=ApsPayload(
                    alert=ApsAlert(title=title, subtitle=subtitle, body=body)
                ),
                image_url=image_url
            )
        )
        
        message = FcmMessage(
            token=token,
            notification=FcmNotification(title=title, body=body),
            data=data,
            android=android_config,
            apns=apns_config
        )
        
        return cls(message=message)


# FCM 批量通知消息（发送给多个用户）
class FcmBatchNotificationMessage(BaseModel):
    registration_tokens: List[str] = Field(..., description="FCM令牌列表")
    notification: FcmNotification = Field(..., description="通知内容")
    data: Optional[FcmData] = Field(None, description="自定义数据")
    android: Optional[AndroidConfig] = Field(None, description="Android特定配置")
    apns: Optional[ApnsConfig] = Field(None, description="iOS特定配置")