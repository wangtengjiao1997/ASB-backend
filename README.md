# Undefined Backend

## 摘要

Undefined Backend 是一个基于 FastAPI 和 MongoDB 的现代化后端项目，采用分层架构设计，提供可扩展、高性能的 API 服务。项目遵循领域驱动设计（DDD）的思想，实现了关注点分离，使代码结构清晰、易于维护和扩展。系统设计考虑了多业务领域的需求，包括用户管理、内容管理以及未来可能的 AI 集成和爬虫功能。

## 项目结构

```
undefined_backend/
├── app/                   # 应用主目录
│   ├── core/              # 核心配置和数据库连接
│   ├── crud/              # 数据访问操作实现
│   ├── domain/            # 核心业务逻辑
│   ├── entities/          # 数据实体定义
│   ├── features/          # API接口和用户交互
│   └── infrastructure/    # 基础设施配置
│   ├── middleware/        # 中间件
│   ├── schemas/           # 数据模式定义
│   ├── utils/             # 通用工具函数
│   └── main.py            # 应用入口
├── logs/                  # 日志文件
└── .env
```

## 关键目录说明

### app/core/

核心配置模块，包含应用程序的基础配置和数据库连接管理。

- `config.py` - 环境变量和应用配置
- `data_source.py` - MongoDB数据库连接和初始化

### app/crud/

数据访问层，封装所有与数据库交互的操作。

- `base_crud.py` - 通用CRUD操作基类
- `user_crud.py` - 用户相关数据操作
- 其他实体的CRUD实现

### app/domain/

- 包含所有核心业务逻辑
- 按照业务领域划分子目录（feed、ai、crawler、realtime）
- 每个领域包含该领域的服务和业务规则

### app/entities/

数据实体定义，对应MongoDB集合的文档模型。

- `base.py` - 基础文档模型，包含通用字段
- `user_entity.py` - 用户实体
- `post_entity.py` - 帖子实体

### app/features/

- 面向HTTP API和用户交互
- 负责路由、请求处理和响应格式化
- 调用domain层服务执行业务逻辑


- `user/` - 用户管理功能
  - `user_router.py` - 用户API路由
  - `user_controller.py` - 请求处理和响应格式化
  - `user_service.py` - 用户业务逻辑
- `post/` - 内容管理功能
  - `post_router.py` - 内容API路由
  - `post_controller.py` - 请求处理
  - `post_service.py` - 内容业务逻辑

### app/infrastructrue/

- 包含与外部系统交互的基础设施代码
- 包括cache、ai、socket和crawlers等技术实现
- 与业务逻辑解耦，提供技术服务

### app/middleware/

中间件组件，处理请求/响应的横切关注点。

- `logging_middleware.py` - 请求日志记录
- `error_handler.py` - 全局异常处理

### app/schemas/

数据传输对象定义，用于API输入验证和输出序列化。

- `user_schema.py` - 用户相关请求/响应模式
- `post_shema.py` - 帖子相关请求/响应模式
- `response_schema.py` - 通用响应格式

## 应用架构

项目采用分层架构，主要分为以下几层：

1. **API层** (Features) - 处理HTTP请求/响应
2. **业务逻辑层** (Services) - 实现业务规则和流程
3. **数据访问层** (CRUD) - 执行数据库操作

每一层都有明确的职责，确保关注点分离：

- **Controllers** 负责处理HTTP请求和构造响应
- **Services** 负责实现业务逻辑
- **CRUD** 负责执行数据库操作

## 启动指南

1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **环境配置**

创建 `.env` 文件：

```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=undefined_backend
DEBUG=True
```

3. **启动服务**

开发环境：
```bash
uvicorn app.main:app --reload
```

生产环境：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. **访问API**

- API文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API响应格式

所有API统一使用以下响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```
