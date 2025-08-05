import boto3
import uuid
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile, HTTPException
import os
from datetime import datetime
from app.core.config import settings
from app.utils.logger_service import logger
import httpx
import tempfile

class S3Service:
    """S3文件上传服务"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET
        self.base_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com"
    
    async def upload_image(
        self, 
        file: UploadFile, 
        folder: str = "images",
        user_id: Optional[str] = None
    ) -> str:
        """
        上传图片到S3
        
        Args:
            file: 上传的文件对象
            folder: S3中的文件夹路径
            user_id: 用户ID，用于组织文件路径
            
        Returns:
            str: 文件的完整URL
        """
        try:
            # 验证文件
            await self._validate_image_file(file)
            
            # 生成文件名
            file_key = self._generate_file_key(file.filename, folder, user_id)
            
            # 重置文件指针
            await file.seek(0)
            
            # 上传到S3
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                file_key,
                ExtraArgs={
                    'ContentType': file.content_type,
                    'ACL': 'public-read',  # 设置为公开读取
                    'CacheControl': 'max-age=31536000',  # 缓存一年
                    'Metadata': {
                        'uploaded_by': user_id or 'anonymous',
                        'uploaded_at': datetime.now().isoformat(),
                        'original_filename': file.filename or 'unknown'
                    }
                }
            )
            
            # 构建完整URL
            file_url = f"{self.base_url}/{file_key}"
            
            logger.info(f"文件上传成功: {file_key} -> {file_url}")
            return file_url
            
        except ClientError as e:
            logger.error(f"S3上传失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"文件上传失败: {str(e)}"
            )
        except Exception as e:
            logger.error(f"文件上传过程中发生错误: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"文件上传失败: {str(e)}"
            )
    
    async def delete_image(self, file_url: str) -> bool:
        """
        删除S3中的图片
        
        Args:
            file_url: 文件的完整URL
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 从URL中提取文件key
            file_key = file_url.replace(f"{self.base_url}/", "")
            
            # 删除文件
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            logger.info(f"文件删除成功: {file_key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3删除失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"文件删除过程中发生错误: {str(e)}")
            return False
    
    async def upload_image_from_url(
        self,
        image_url: str,
        folder: str = "images",
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        从URL下载图片并上传到S3

        Args:
            image_url: 图片的URL
            folder: S3中的文件夹路径
            user_id: 用户ID，用于组织文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, S3 URL或错误信息)
        """
        temp_file = None
        upload_file = None
        try:
            # 下载图片
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                if response.status_code != 200:
                    return None

                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.write(response.content)
                temp_file.close()

                # 获取文件名和内容类型
                filename = image_url.split('/')[-1]
                content_type = response.headers.get("content-type", "image/jpeg")

                # 创建 UploadFile 对象
                upload_file = UploadFile(
                    filename=filename,
                    file=open(temp_file.name, "rb"),
                    content_type=content_type
                )

                # 上传到S3
                s3_url = await self.upload_image(
                    file=upload_file,
                    folder=folder,
                    user_id=user_id
                )

                return s3_url

        except Exception as e:
            logger.error(f"处理图片失败: {str(e)}")
            return None

        finally:
            # 清理资源
            if upload_file:
                await upload_file.close()
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def _generate_file_key(
        self, 
        filename: str, 
        folder: str, 
        user_id: Optional[str] = None
    ) -> str:
        """生成S3文件key"""
        # 获取文件扩展名
        file_extension = os.path.splitext(filename)[1].lower()
        
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # 构建文件路径
        if user_id:
            # 按用户组织文件：folder/user_id/YYYY/MM/filename
            date_path = datetime.now().strftime("%Y/%m")
            file_key = f"{folder}/{user_id}/{date_path}/{unique_filename}"
        else:
            # 通用路径：folder/YYYY/MM/DD/filename
            date_path = datetime.now().strftime("%Y/%m/%d")
            file_key = f"{folder}/{date_path}/{unique_filename}"
        
        return file_key
    
    async def _validate_image_file(self, file: UploadFile):
        """验证上传的图片文件"""
        # 检查文件大小（限制为5MB）
        max_size = 5 * 1024 * 1024  # 5MB
        file_size = 0
        
        # 重置文件指针并计算大小
        await file.seek(0)
        content = await file.read()
        file_size = len(content)
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件太大，最大允许5MB，当前文件大小: {file_size / 1024 / 1024:.2f}MB"
            )
        
        # 检查文件类型
        allowed_types = [
            'image/jpeg', 'image/jpg', 'image/png', 
            'image/gif', 'image/webp'
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}，支持的类型: {', '.join(allowed_types)}"
            )
        
        # 检查文件扩展名
        if file.filename:
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            file_extension = os.path.splitext(file.filename)[1].lower()
            
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件扩展名: {file_extension}，支持的扩展名: {', '.join(allowed_extensions)}"
                )
        
        # 重置文件指针，以便后续使用
        await file.seek(0)


# 创建全局实例
s3_service = S3Service()