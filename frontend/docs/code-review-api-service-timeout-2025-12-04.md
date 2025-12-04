# 代码审查报告：ApiService 超时配置修改

**文件**: `frontend/src/services/api.ts`  
**审查日期**: 2025-12-04  
**修改内容**: 将 HTTP 超时时间从 30 秒增加到 180 秒（3 分钟）

---

## 1. 代码异味：未使用的成员变量

### 问题位置
```typescript
private userTier: string = 'professional';  // 改为专业会员以测试场景融合
```

### 为什么是问题
- **TypeScript 编译器警告**：`'userTier' is declared but its value is never read`
- **死代码**：变量被声明和赋值，但从未在类中被读取使用
- **内存浪费**：虽然影响微小，但保留无用代码会增加维护负担
- **误导性**：其他开发者可能认为这个变量有实际用途

### 改进建议
移除未使用的 `userTier` 成员变量，或者在需要时使用它：

**方案 A：移除未使用变量**
```typescript
class ApiService {
  private client: AxiosInstance;
  private userId: string = 'demo-user';
  // 移除 userTier，因为 setUser 方法直接操作 headers

  setUser(userId: string, tier: 'free' | 'basic' | 'professional' = 'basic') {
    this.userId = userId;
    this.client.defaults.headers['X-User-Id'] = userId;
    this.client.defaults.headers['X-User-Tier'] = tier;
  }
}
```

**方案 B：使用变量（如果需要在其他地方访问）**
```typescript
class ApiService {
  private client: AxiosInstance;
  private userId: string = 'demo-user';
  private userTier: 'free' | 'basic' | 'professional' = 'professional';

  // 添加 getter 方法
  getUserTier(): string {
    return this.userTier;
  }

  setUser(userId: string, tier: 'free' | 'basic' | 'professional' = 'basic') {
    this.userId = userId;
    this.userTier = tier;
    this.client.defaults.headers['X-User-Id'] = userId;
    this.client.defaults.headers['X-User-Tier'] = tier;
  }
}
```

### 预期收益
- 消除 TypeScript 编译警告
- 代码更简洁，减少维护负担

### 优先级
**高** - 编译器警告应尽快修复

---

## 2. 设计建议：超时配置硬编码

### 问题位置
```typescript
constructor() {
  this.client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 180000, // 3 minutes for batch image generation
    // ...
  });
}
```

### 为什么是问题
- **配置硬编码**：超时时间直接写在代码中，修改需要重新构建
- **不同操作需要不同超时**：批量生成需要 3 分钟，但简单的模板查询可能只需要 10 秒
- **全局超时过长**：对于快速失败的场景（如网络断开），用户需要等待 3 分钟才能看到错误

### 改进建议
1. 将超时配置提取到环境变量
2. 为不同类型的请求设置不同的超时时间

```typescript
// 超时配置常量
const TIMEOUT_CONFIG = {
  default: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,      // 30 秒
  generation: Number(import.meta.env.VITE_API_GENERATION_TIMEOUT) || 180000,  // 3 分钟
  upload: Number(import.meta.env.VITE_API_UPLOAD_TIMEOUT) || 60000,  // 1 分钟
};

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: TIMEOUT_CONFIG.default,
      // ...
    });
  }

  async generatePoster(request: PosterGenerationRequest): Promise<PosterGenerationResponse> {
    const response = await this.client.post<PosterGenerationResponse>(
      '/api/poster/generate',
      request,
      { timeout: TIMEOUT_CONFIG.generation }  // 使用生成专用超时
    );
    return response.data;
  }

  async sceneFusion(request: SceneFusionRequest): Promise<SceneFusionResponse> {
    const response = await this.client.post<SceneFusionResponse>(
      '/api/scene-fusion',
      request,
      { timeout: TIMEOUT_CONFIG.generation }  // 使用生成专用超时
    );
    return response.data;
  }
}
```

### 预期收益
- 配置可通过环境变量调整，无需修改代码
- 不同操作使用合适的超时时间
- 快速操作能更快地反馈错误

### 优先级
**中** - 当前实现可用，但可维护性和用户体验可以改进

---

## 3. 健壮性：缺少错误处理

### 问题位置
```typescript
async generatePoster(request: PosterGenerationRequest): Promise<PosterGenerationResponse> {
  const response = await this.client.post<PosterGenerationResponse>(
    '/api/poster/generate',
    request
  );
  return response.data;
}
```

### 为什么是问题
- **无统一错误处理**：每个调用方都需要自己处理错误
- **错误信息不友好**：Axios 原始错误对用户不友好
- **缺少重试机制**：网络抖动时直接失败

### 改进建议
添加 Axios 拦截器进行统一错误处理：

```typescript
class ApiService {
  constructor() {
    this.client = axios.create({
      // ...
    });

    // 响应拦截器 - 统一错误处理
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.code === 'ECONNABORTED') {
          return Promise.reject(new Error('请求超时，请稍后重试'));
        }
        if (error.response) {
          const { status, data } = error.response;
          switch (status) {
            case 401:
              return Promise.reject(new Error('未授权，请重新登录'));
            case 429:
              return Promise.reject(new Error('请求过于频繁，请稍后重试'));
            case 500:
              return Promise.reject(new Error('服务器错误，请稍后重试'));
            default:
              return Promise.reject(new Error(data?.message || '请求失败'));
          }
        }
        return Promise.reject(new Error('网络连接失败，请检查网络'));
      }
    );
  }
}
```

### 预期收益
- 统一的错误处理逻辑
- 用户友好的错误提示
- 减少调用方的重复代码

### 优先级
**中** - 提升用户体验和代码可维护性

---

## 4. 安全性：硬编码的用户凭证

### 问题位置
```typescript
private userId: string = 'demo-user';
private userTier: string = 'professional';

constructor() {
  this.client = axios.create({
    // ...
    headers: {
      'X-User-Id': this.userId,
      'X-User-Tier': 'professional',  // 硬编码为 professional
    },
  });
}
```

### 为什么是问题
- **硬编码凭证**：用户 ID 和会员等级直接写在代码中
- **不一致性**：`userTier` 变量值与 headers 中的值可能不同步
- **安全风险**：生产环境可能意外使用测试凭证

### 改进建议
使用环境变量或延迟初始化：

```typescript
class ApiService {
  private client: AxiosInstance;
  private userId: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: TIMEOUT_CONFIG.default,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 开发环境自动设置测试用户
    if (import.meta.env.DEV) {
      this.setUser(
        import.meta.env.VITE_DEV_USER_ID || 'demo-user',
        (import.meta.env.VITE_DEV_USER_TIER as 'free' | 'basic' | 'professional') || 'professional'
      );
    }
  }

  isAuthenticated(): boolean {
    return this.userId !== null;
  }
}
```

### 预期收益
- 开发/生产环境配置分离
- 避免意外使用测试凭证
- 更清晰的认证状态管理

### 优先级
**低** - 当前是开发阶段，但上线前需要处理

---

## 5. 做得好的地方 ✓

### 5.1 清晰的类型定义
使用 TypeScript 泛型确保类型安全：
```typescript
const response = await this.client.post<PosterGenerationResponse>(...)
```

### 5.2 良好的文档注释
每个方法都有 JSDoc 注释和需求追溯：
```typescript
/**
 * 生成海报
 * Requirements: 1.1, 1.2, 2.1, 2.2
 */
```

### 5.3 单例模式导出
提供单例实例，避免重复创建：
```typescript
export const apiService = new ApiService();
export default apiService;
```

### 5.4 合理的超时调整
将超时从 30 秒增加到 180 秒是合理的，因为批量图像生成确实需要更长时间。注释也清楚说明了原因。

### 5.5 灵活的用户设置
`setUser` 方法允许动态更改用户信息，支持不同会员等级测试。

---

## 总结

| 优先级 | 问题 | 建议 |
|--------|------|------|
| 高 | 未使用的 userTier 变量 | 移除或正确使用 |
| 中 | 超时配置硬编码 | 提取到环境变量，按操作类型区分 |
| 中 | 缺少统一错误处理 | 添加 Axios 拦截器 |
| 低 | 硬编码用户凭证 | 使用环境变量配置 |

本次超时修改本身是合理的，解决了批量生成时的超时问题。建议的改进主要是为了提高代码的可维护性和健壮性。
