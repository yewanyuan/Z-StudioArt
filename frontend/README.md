# PopGraph Frontend

爆款图 - AI 图文一体化生成平台前端

## 技术栈

- React 19
- TypeScript
- Vite
- TailwindCSS
- Vitest + fast-check (测试)

## 开发环境设置

### 安装依赖

```bash
cd frontend
npm install
```

### 运行开发服务器

```bash
npm run dev
```

开发服务器默认配置：
- 地址：`http://localhost:5173`
- 支持外部访问：`http://<your-ip>:5173`（已配置 `host: '0.0.0.0'`）

> 外部访问功能便于在局域网内的其他设备（如手机）上预览和测试。

### 运行测试

```bash
# 运行所有测试
npm test

# 监听模式
npm run test:watch
```

### 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── components/    # React 组件
│   ├── services/      # API 服务
│   │   └── api.ts     # API 客户端（含用户身份管理）
│   ├── types/         # TypeScript 类型定义
│   ├── utils/         # 工具函数
│   ├── test/          # 测试配置
│   ├── App.tsx        # 主应用组件
│   └── main.tsx       # 入口文件
├── tests/
│   ├── unit/          # 单元测试
│   └── property/      # 属性测试
└── package.json
```

## 类型定义 (`src/types/index.ts`)

前端类型定义与后端 `schemas.py` 保持一致，确保前后端数据结构统一。

### 枚举类型

| 类型 | 可选值 | 说明 |
|------|--------|------|
| `MembershipTier` | `'free'` \| `'basic'` \| `'professional'` | 会员等级 |
| `TemplateCategory` | `'promotional'` \| `'premium'` \| `'holiday'` | 模板分类 |
| `HolidayType` | `'spring_festival'` \| `'valentines'` \| `'double_eleven'` | 节日类型 |
| `AspectRatio` | `'1:1'` \| `'9:16'` \| `'16:9'` | 输出尺寸比例 |
| `Language` | `'zh'` \| `'en'` | 文案语言 |

### 海报生成类型

| 接口 | 用途 |
|------|------|
| `PosterGenerationRequest` | 海报生成请求参数 |
| `GeneratedImage` | 生成的图像信息（含可选 Base64 数据） |
| `PosterGenerationResponse` | 海报生成响应 |

#### GeneratedImage 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 图像唯一标识 |
| `url` | string | 是 | 图像 URL（推荐使用） |
| `thumbnail_url` | string | 是 | 缩略图 URL |
| `has_watermark` | boolean | 是 | 是否有水印 |
| `width` | number | 是 | 图像宽度 |
| `height` | number | 是 | 图像高度 |
| `image_base64` | string | 否 | 图像 Base64 编码数据 |

### 模板类型

| 接口 | 用途 |
|------|------|
| `PromptModifiers` | 模板 Prompt 修饰参数 |
| `Template` | 预设商业模板定义 |

### 场景融合类型

| 接口 | 用途 |
|------|------|
| `SceneFusionRequest` | 场景融合请求参数 |
| `SceneFusionResponse` | 场景融合响应 |

### 通用类型

| 接口 | 用途 |
|------|------|
| `ApiError` | API 错误响应格式 |
| `GenerationState` | UI 生成状态管理 |

## API 服务 (`src/services/api.ts`)

封装与后端的 HTTP 通信，提供类型安全的 API 调用接口。

### 用户身份管理

API 服务内置用户身份管理功能，通过 HTTP 请求头传递用户信息：

| 请求头 | 说明 | 默认值 |
|--------|------|--------|
| `X-User-Id` | 用户 ID | `demo-user` |
| `X-User-Tier` | 会员等级 | `basic` |

**使用示例：**

```typescript
import { apiService } from './services/api';

// 设置用户信息（登录后调用）
apiService.setUser('user-123', 'professional');

// 后续 API 调用会自动携带用户信息
const response = await apiService.generatePoster({
  scene_description: '夏日海滩促销',
  marketing_text: '限时特惠',
  language: 'zh',
  aspect_ratio: '1:1',
});
```

### API 方法

| 方法 | 功能 | 对应需求 |
|------|------|----------|
| `setUser(userId, tier)` | 设置用户身份信息 | 7.1, 7.2, 7.3 |
| `generatePoster(request)` | 生成商业海报 | 1.1, 1.2, 2.1, 2.2 |
| `getTemplates(category?)` | 获取模板列表 | 3.1, 3.2, 3.3 |
| `sceneFusion(request)` | 商品图场景融合 | 4.1, 4.2, 4.3 |
| `uploadProductImage(file)` | 上传商品图片 | 4.1 |

### 配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `VITE_API_BASE_URL` | 后端 API 地址 | `http://localhost:8000` |

### 超时配置

API 客户端默认超时时间为 **180 秒（3 分钟）**，以支持批量图像生成等耗时较长的操作。

| 操作类型 | 超时时间 | 说明 |
|----------|----------|------|
| 所有请求 | 180 秒 | 批量生成（4 张预览图）可能需要较长时间 |

> **注意**：如果遇到超时错误，请检查后端服务是否正常运行，或网络连接是否稳定。
