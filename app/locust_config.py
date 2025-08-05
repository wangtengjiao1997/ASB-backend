"""
Locust压测配置文件
用于测试1万DAU的性能表现
"""

# 测试配置
TEST_CONFIG = {
    # 基础配置
    "host": "http://localhost:8000",  # 替换为你的API地址
    "users": 10000,  # 目标并发用户数 (模拟1万DAU)
    "spawn_rate": 100,  # 每秒启动用户数
    "run_time": "30m",  # 测试运行时间
    
    # 用户行为配置
    "user_behavior": {
        "browse_weight": 20,  # 浏览权重
        "interaction_weight": 10,  # 互动权重  
        "content_creation_weight": 2,  # 内容创建权重
    },
    
    # 测试用户数据
    "test_users": [
        {"email": "test1@example.com", "password": "Test123456!"},
        {"email": "test2@example.com", "password": "Test123456!"},
        {"email": "test3@example.com", "password": "Test123456!"},
        {"email": "test4@example.com", "password": "Test123456!"},
        {"email": "test5@example.com", "password": "Test123456!"},
    ],
    
    # 性能指标目标
    "performance_targets": {
        "response_time_95th": 2000,  # 95%响应时间 < 2秒
        "response_time_avg": 500,    # 平均响应时间 < 500ms
        "error_rate": 0.01,          # 错误率 < 1%
        "requests_per_second": 1000, # 目标RPS
    }
}

# API端点权重配置
API_WEIGHTS = {
    "auth": 5,           # 认证相关
    "posts_browse": 25,  # 浏览帖子
    "posts_detail": 15,  # 帖子详情
    "agents_browse": 15, # 浏览agent
    "agents_detail": 10, # agent详情
    "interactions": 20,  # 互动(点赞、评论、关注)
    "feeds": 8,          # 动态流
    "create_content": 2, # 创建内容
}