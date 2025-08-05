import re

def map_cdn_url(url: str) -> str:
    """
    将 S3 URL 转换为 CDN URL，返回带有 SIZE_PLACEHOLDER 的 URL
    
    Args:
        url (str): S3 URL，支持两种格式：
            - s3://bucket/path/to/file
            - https://bucket.s3.region.amazonaws.com/path/to/file
    
    Returns:
        str: 带有 SIZE_PLACEHOLDER 的 CDN URL
    
    Examples:
        >>> map_cdn_url('s3://tapiavatar/avatars/image.jpg')
        'https://d2i996nisgnhsm.cloudfront.net/{SIZE_PLACEHOLDER}/avatars/image.jpg'
        >>> map_cdn_url('https://tapiavatar.s3.us-east-1.amazonaws.com/avatars/image.jpg')
        'https://d2i996nisgnhsm.cloudfront.net/{SIZE_PLACEHOLDER}/avatars/image.jpg'
    """
    # CDN 域名
    CDN_DOMAIN = "d2i996nisgnhsm.cloudfront.net"
    
    # 定义正则表达式模式
    s3_protocol_pattern = r'^s3://([^/]+)/(.+)$'
    s3_http_pattern = r'^https://([^/]+)\.s3\.[^/]+\.amazonaws\.com/(.+)$'
    
    # 尝试匹配 s3:// 格式
    match = re.match(s3_protocol_pattern, url)
    if not match:
        # 尝试匹配 https:// 格式
        match = re.match(s3_http_pattern, url)
    
    if match:
        # 提取文件路径（groups()[1] 是第二个捕获组，即文件路径部分）
        path = match.groups()[1]
    else:
        # 如果都不匹配，返回原始路径
        path = url.split('/')[-1]
    
    # 构建带有 SIZE_PLACEHOLDER 的 URL
    cdn_url = f"https://{CDN_DOMAIN}/{{SIZE_PLACEHOLDER}}/{path}"
    
    return cdn_url