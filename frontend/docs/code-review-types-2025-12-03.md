# 代码审查：frontend/src/types/index.ts

**审查日期**: 2025-12-03  
**文件**: `frontend/src/types/index.ts`  
**审查结论**: 整体质量良好，有少量优化空间

---

## 1. 建议：使用 `const` 枚举或对象常量

### 问题位置
```typescript
export type MembershipTier = 'free' | 'basic' | 'professional';
export type AspectRatio = '1:1' | '9:16' | '16:9';
```

### 为什么是问题
- 字面量联合类型无法在运行时遍历或验证
- 如果需要在 UI 中展示选项列表，需要重复定义这些值

### 改进建议
```typescript
// 方案 A：使用 as const 对象（推荐）
export const MEMBERSHIP_TIERS = {
  FREE: 'free',
  BASIC: 'basic',
  PROFESSIONAL: 'professional',
} as const;
export type MembershipTier = typeof MEMBERSHIP_TIERS[keyof typeof MEMBERSHIP_TIERS];

export const ASPECT_RATIOS = {
  SQUARE: '1:1',
  MOBILE: '9:16',
  VIDEO: '16:9',
} as const;
export type AspectRatio = typeof ASPECT_RATIOS[keyof typeof ASPECT_RATIOS];
```

### 预期收益
- 运行时可访问枚举值列表
- 便于 UI 组件渲染选项
- 单一数据源，减少重复

---

## 2. 建议：添加 JSDoc 注释

### 问题位置
接口定义缺少文档注释

### 为什么是问题
- 其他开发者需要查看后端代码才能理解字段含义
- IDE 无法提供有意义的悬停提示

### 改进建议
```typescript
export interface PosterGenerationRequest {
  /** 画面描述，描述海报的视觉场景 */
  scene_description: string;
  /** 营销文案，将渲染在海报上的文字 */
  marketing_text: string;
  /** 文案语言：zh-中文，en-英文 */
  language: Language;
  /** 可选的模板 ID */
  template_id?: string;
  /** 输出图片宽高比 */
  aspect_ratio: AspectRatio;
  /** 生成数量：1-单张，4-预览模式 */
  batch_size: 1 | 4;
}
```

### 预期收益
- 提升代码可读性
- IDE 智能提示更友好
- 减少查阅后端代码的需要

---

## 3. 建议：考虑拆分类型文件

### 问题位置
所有类型定义在单一文件中

### 为什么是问题
- 随着项目增长，文件会变得过大
- 不同功能模块的类型混在一起

### 改进建议
```
frontend/src/types/
├── index.ts          # 统一导出
├── poster.types.ts   # 海报生成相关
├── template.types.ts # 模板相关
├── scene.types.ts    # 场景融合相关
└── common.types.ts   # 通用类型（枚举、错误等）
```

### 预期收益
- 更好的代码组织
- 便于按需导入
- 降低合并冲突概率

**注意**: 当前文件约 100 行，暂时不需要拆分，可作为未来扩展的参考。

---

## 4. 小问题：命名风格不一致

### 问题位置
```typescript
// 后端风格 (snake_case)
scene_description: string;
marketing_text: string;

// 前端通常使用 camelCase
```

### 分析
这是为了与后端 API 保持一致，属于合理的设计决策。如果需要前端风格，可以：

```typescript
// 定义 API 类型（与后端一致）
export interface PosterGenerationRequestDTO {
  scene_description: string;
  marketing_text: string;
  // ...
}

// 定义前端类型（camelCase）
export interface PosterGenerationForm {
  sceneDescription: string;
  marketingText: string;
  // ...
}

// 提供转换函数
export const toDTO = (form: PosterGenerationForm): PosterGenerationRequestDTO => ({
  scene_description: form.sceneDescription,
  // ...
});
```

### 建议
当前保持与后端一致是合理的，无需修改。如果团队有强烈的前端命名规范要求，可以考虑上述方案。

---

## 总结

| 类别 | 评分 | 说明 |
|------|------|------|
| 代码组织 | ⭐⭐⭐⭐ | 分组清晰，注释分隔符有效 |
| 类型安全 | ⭐⭐⭐⭐⭐ | 字面量类型使用得当 |
| 可读性 | ⭐⭐⭐ | 缺少 JSDoc，但结构清晰 |
| 可维护性 | ⭐⭐⭐⭐ | 与后端同步，单一数据源 |
| 最佳实践 | ⭐⭐⭐⭐ | 符合 TypeScript 惯例 |

**整体评价**: 这是一个质量良好的类型定义文件，建议优先添加 JSDoc 注释以提升开发体验。
