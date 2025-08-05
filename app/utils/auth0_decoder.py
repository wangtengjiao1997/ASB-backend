import hashlib
import base64


def token_to_key_16char(token, prefix="tk:"):
    """
    将JWT/JWE令牌转换为16字符的短key
    
    方法：使用SHA-256哈希后取前12字节，进行base64编码得到16个字符
    
    Args:
        token: 原始令牌
        prefix: key前缀(可选)
        
    Returns:
        16字符的短key，加上前缀
    """
    # 计算token的SHA-256哈希
    hash_obj = hashlib.sha256(token.encode())
    hash_digest = hash_obj.digest()
    
    # 取前12字节(96位)，Base64编码后正好是16个字符
    # (每6位编码为1个字符，96/6=16)
    short_bytes = hash_digest[:12]
    
    # Base64编码(使用URL安全的变体，避免特殊字符)
    encoded = base64.urlsafe_b64encode(short_bytes).decode()
    
    # Base64编码会在末尾添加等号填充，需要去掉
    encoded = encoded.rstrip('=')
    
    # 添加前缀
    return encoded