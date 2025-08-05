from datetime import datetime
import json
def json_serializer(obj):
    """处理特殊类型的JSON序列化"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    # 处理其他不可序列化类型
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable") 

def dumps(obj, **kwargs):
    """
    使用自定义序列化器将对象转换为JSON字符串
    """
    return json.dumps(obj, default=json_serializer, **kwargs)

def validate_json(json_str):
    """
    验证JSON字符串是否有效
    """
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False