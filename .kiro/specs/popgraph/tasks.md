# Implementation Plan

## Phase 1: 项目初始化与核心基础设施

- [x] 1. 初始化项目结构和依赖配置
  - [x] 1.1 创建后端项目结构 (Python + FastAPI)
    - 创建 `backend/` 目录结构：`app/`, `tests/`, `conftest.py`
    - 创建 `pyproject.toml` 配置 Poetry 依赖管理
    - 添加依赖：fastapi, uvicorn, pydantic, sqlalchemy, redis, pillow, hypothesis, pytest
    - _Requirements: 2.1, 2.3_
  - [x] 1.2 创建前端项目结构 (React + TypeScript)
    - 使用 Vite 初始化 React + TypeScript 项目
    - 配置 TailwindCSS
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 2. 实现核心数据模型和 Schema
  - [x] 2.1 创建 Pydantic Schema 定义
    - 实现 `PosterGenerationRequest`, `PosterGenerationResponse`, `GeneratedImage`
    - 实现 `Template`, `PromptModifiers`
    - 实现 `ContentFilterResult`, `RateLimitResult`
    - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.3_
  - [x] 2.2 创建 SQLAlchemy 数据库模型
    - 实现 `User`, `GenerationRecord`, `TemplateRecord` 模型
    - 配置数据库连接和迁移
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

## Phase 2: Prompt Builder 核心模块

- [x] 3. 实现 Prompt Builder
  - [x] 3.1 实现基础 Prompt 构建逻辑
    - 创建 `backend/app/utils/prompt_builder.py`
    - 实现 `build_poster_prompt()` 方法
    - 实现 `inject_text_placement()` 方法，支持中英文文本嵌入
    - _Requirements: 1.1, 1.2, 1.4, 1.5_
  - [x] 3.2 编写 Property 1 属性测试：文本渲染正确性
    - **Property 1: 文本渲染正确性**
    - **Validates: Requirements 1.1, 1.2**
    - 使用 hypothesis 生成随机中英文文本
    - 验证生成的 prompt 包含原始文本
  - [x] 3.3 实现模板参数合并逻辑
    - 实现 `apply_modifiers()` 方法
    - 支持风格关键词、配色方案、排版提示、字体风格的合并
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [x] 3.4 编写 Property 4 属性测试：模板参数应用正确性
    - **Property 4: 模板参数应用正确性**
    - **Validates: Requirements 3.1, 3.2, 3.3**
    - 生成随机模板配置，验证所有参数出现在最终 prompt
  - [x] 3.5 编写 Property 5 属性测试：模板与用户输入组合完整性
    - **Property 5: 模板与用户输入组合完整性**
    - **Validates: Requirements 3.4**
    - 生成随机模板和用户输入，验证两者都出现在最终 prompt

- [x] 4. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

## Phase 3: 内容过滤服务

- [x] 5. 实现 Content Filter Service
  - [x] 5.1 创建敏感词过滤服务
    - 创建 `backend/app/services/content_filter.py`
    - 实现 `check_content()` 方法
    - 实现敏感词库加载和匹配逻辑
    - _Requirements: 6.1_
  - [x] 5.2 编写 Property 7 属性测试：敏感词过滤有效性
    - **Property 7: 敏感词过滤有效性**
    - **Validates: Requirements 6.1**
    - 生成包含随机敏感词的输入，验证过滤结果正确
  - [x] 5.3 编写单元测试
    - 测试已知敏感词被正确过滤
    - 测试正常内容通过过滤
    - _Requirements: 6.1_

## Phase 4: 限流与会员系统

- [x] 6. 实现 Rate Limiter
  - [x] 6.1 创建限流服务
    - 创建 `backend/app/utils/rate_limiter.py`
    - 实现 `check_limit()`, `increment_usage()`, `get_remaining_quota()` 方法
    - 集成 Redis 进行计数存储
    - _Requirements: 7.2_
  - [x] 6.2 编写 Property 9 属性测试：免费用户每日限额
    - **Property 9: 免费用户每日限额**
    - **Validates: Requirements 7.2**
    - 模拟随机使用次数，验证限额逻辑正确

- [x] 7. 实现会员权限服务
  - [x] 7.1 创建会员权限检查逻辑
    - 创建 `backend/app/services/membership_service.py`
    - 实现水印规则判断
    - 实现功能权限检查
    - _Requirements: 7.1, 7.3, 7.4_
  - [x] 7.2 编写 Property 8 属性测试：会员等级水印规则
    - **Property 8: 会员等级水印规则**
    - **Validates: Requirements 7.1, 7.3**
    - 生成随机会员等级，验证水印标记符合规则
  - [x] 7.3 编写 Property 10 属性测试：专业会员功能权限
    - **Property 10: 专业会员功能权限**
    - **Validates: Requirements 7.4**
    - 生成随机会员等级，验证场景融合权限正确

- [x] 8. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

## Phase 5: 模板服务

- [x] 9. 实现 Template Service
  - [x] 9.1 创建模板服务
    - 创建 `backend/app/services/template_service.py`
    - 实现 `list_templates()`, `get_template()`, `apply_template()` 方法
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [x] 9.2 创建预设模板数据
    - 创建促销类模板（红色背景、爆炸贴纸风格、大字号）
    - 创建高级类模板（极简留白、影棚光效、黑金配色）
    - 创建节日类模板（春节、情人节、双十一）
    - _Requirements: 3.1, 3.2, 3.3_
  - [x] 9.3 编写单元测试
    - 测试模板加载正确
    - 测试模板参数合并逻辑
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

## Phase 6: Z-Image-Turbo 客户端

- [x] 10. 实现 Z-Image-Turbo Client
  - [x] 10.1 创建 AI 模型客户端
    - 创建 `backend/app/clients/zimage_client.py`
    - 实现 `generate_image()`, `generate_batch()` 方法
    - 实现图像尺寸计算逻辑
    - _Requirements: 2.1, 2.2, 5.1, 5.2, 5.3_
  - [x] 10.2 编写 Property 6 属性测试：输出尺寸正确性
    - **Property 6: 输出尺寸正确性**
    - **Validates: Requirements 5.1, 5.2, 5.3**
    - 生成随机尺寸请求，验证输出尺寸符合比例
  - [x] 10.3 编写 Property 3 属性测试：批量生成数量一致性
    - **Property 3: 批量生成数量一致性**
    - **Validates: Requirements 2.2**
    - 验证 batch_size=4 时返回 4 张图

- [x] 11. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

## Phase 7: 海报生成服务

- [x] 12. 实现 Poster Generation Service
  - [x] 12.1 创建海报生成服务
    - 创建 `backend/app/services/poster_service.py`
    - 整合 PromptBuilder, ContentFilter, TemplateService, ZImageClient
    - 实现完整的海报生成流程
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2_
  - [x] 12.2 实现水印添加逻辑
    - 使用 Pillow 实现水印叠加
    - 根据会员等级决定是否添加水印
    - _Requirements: 7.1, 7.3_
  - [x] 12.3 编写集成测试
    - 测试完整的海报生成流程
    - 测试错误处理逻辑
    - _Requirements: 1.1, 1.2, 2.1, 2.2_

## Phase 8: 场景融合服务

- [x] 13. 实现 Scene Fusion Service
  - [x] 13.1 创建场景融合服务
    - 创建 `backend/app/services/scene_fusion_service.py`
    - 实现 `extract_product()` 方法（商品主体提取）
    - 实现 `fuse_with_scene()` 方法
    - _Requirements: 4.1, 4.2, 4.3_
  - [x] 13.2 编写单元测试
    - 测试商品提取逻辑
    - 测试场景融合逻辑
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 14. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

## Phase 9: API 路由层

- [x] 15. 实现 FastAPI 路由
  - [x] 15.1 创建海报生成 API
    - 创建 `backend/app/api/poster.py`
    - 实现 `POST /api/poster/generate` 端点
    - 集成认证、限流、内容过滤中间件
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 6.1, 7.1, 7.2, 7.3_
  - [x] 15.2 创建模板 API
    - 创建 `backend/app/api/templates.py`
    - 实现 `GET /api/templates` 端点
    - _Requirements: 3.1, 3.2, 3.3_
  - [x] 15.3 创建场景融合 API
    - 创建 `backend/app/api/scene_fusion.py`
    - 实现 `POST /api/scene-fusion` 端点
    - 添加专业会员权限检查
    - _Requirements: 4.1, 4.2, 4.3, 7.4_
  - [x] 15.4 编写 API 集成测试
    - 测试各端点的请求/响应
    - 测试错误处理
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 6.1, 7.1_

## Phase 10: 前端实现

- [x] 16. 实现前端核心组件
  - [x] 16.1 创建海报生成页面
    - 实现场景描述输入框
    - 实现文案输入框
    - 实现模板选择器
    - 实现尺寸选择器
    - _Requirements: 1.1, 3.1, 5.1, 5.2, 5.3_
  - [x] 16.2 创建结果展示组件
    - 实现 4 张预览图展示
    - 实现图片下载功能
    - _Requirements: 2.2_
  - [x] 16.3 创建商品图上传组件
    - 实现图片上传和预览
    - 实现场景描述输入
    - _Requirements: 4.1, 4.2_

- [x] 17. Final Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.
