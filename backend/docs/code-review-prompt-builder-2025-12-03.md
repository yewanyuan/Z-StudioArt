# 代码审查报告: prompt_builder.py

**文件**: `backend/app/utils/prompt_builder.py`  
**审查日期**: 2025-12-03  
**审查结论**: 整体质量良好，结构清晰，有几处可优化

---

## ✅ 做得好的地方

1. **文档完善**: 模块级文档、类文档、方法文档都很完整，包含 Args、Returns 和 Requirements 引用
2. **类型注解**: 使用了 `Literal`、`Optional` 等类型注解，提高代码可读性
3. **单一职责**: `PromptBuilder` 类专注于 prompt 构建，职责清晰
4. **常量提取**: `BASE_PROMPT_TEMPLATE` 和 `TEXT_PLACEMENT_TEMPLATES` 作为类常量，便于维护

---

## ~~问题 1: 导入路径错误~~ ✅ 已修复

此问题已于 2025-12-03 修复。当前代码使用正确的导入路径：

```python
from app.models.schemas import (
    PosterGenerationRequest,
    PromptModifiers,
)
```

---

## 问题 2: 魔法字符串散落

### 位置
```python
TEXT_PLACEMENT_TEMPLATES = {
    "zh": '中文文字 "{text}" ...',
    "en": 'English text "{text}" ...',
}

# 以及方法参数中
language: Literal["zh", "en"]
```

### 为什么是问题
- `"zh"` 和 `"en"` 作为字符串字面量多处重复
- 如果需要添加新语言，需要修改多处
- 缺乏类型安全

### 改进建议
```python
from enum import Enum

class SupportedLanguage(str, Enum):
    """支持的语言枚举"""
    CHINESE = "zh"
    ENGLISH = "en"

# 或者复用 schemas.py 中已有的定义，创建类型别名
Language = Literal["zh", "en"]

TEXT_PLACEMENT_TEMPLATES: dict[str, str] = {
    "zh": '中文文字 "{text}" 清晰渲染，文字排版美观，避免遮挡主体',
    "en": 'English text "{text}" clearly rendered, beautiful typography, avoid obscuring main subject',
}
```

### 预期收益
- 单点维护语言配置
- 更好的 IDE 支持

---

## 问题 3: apply_modifiers 缺少空值保护

### 位置
```python
def apply_modifiers(self, modifiers: PromptModifiers) -> str:
    parts = []
    
    if modifiers.style_keywords:
        parts.append(", ".join(modifiers.style_keywords))
    # ...
```

### 为什么是问题
- 虽然检查了 `if modifiers.style_keywords`，但如果 `style_keywords` 包含空字符串元素，会产生 `", , keyword"` 这样的结果
- `color_scheme`、`layout_hints`、`font_style` 如果是空字符串 `""`，条件判断为 `False`，但如果是空格 `" "`，会通过检查

### 改进建议
```python
def apply_modifiers(self, modifiers: PromptModifiers) -> str:
    """Apply template modifiers to generate prompt additions."""
    parts = []
    
    # 过滤空字符串并合并风格关键词
    if modifiers.style_keywords:
        valid_keywords = [kw.strip() for kw in modifiers.style_keywords if kw.strip()]
        if valid_keywords:
            parts.append(", ".join(valid_keywords))
    
    # 使用 strip() 确保非空白字符串
    if modifiers.color_scheme and modifiers.color_scheme.strip():
        parts.append(f"color scheme: {modifiers.color_scheme.strip()}")
    
    if modifiers.layout_hints and modifiers.layout_hints.strip():
        parts.append(f"layout: {modifiers.layout_hints.strip()}")
    
    if modifiers.font_style and modifiers.font_style.strip():
        parts.append(f"font style: {modifiers.font_style.strip()}")
    
    return ", ".join(parts)
```

### 预期收益
- 防止生成包含多余逗号或空白的 prompt
- 提高生成 prompt 的质量

---

## 问题 4: 缺少输入验证

### 位置
```python
def inject_text_placement(
    self,
    base_prompt: str,
    text: str,
    language: Literal["zh", "en"],
) -> str:
```

### 为什么是问题
- 没有验证 `text` 是否为空或仅包含空白
- 空文本会生成 `中文文字 "" 清晰渲染...` 这样无意义的 prompt
- 可能浪费 AI 模型调用资源

### 改进建议
```python
def inject_text_placement(
    self,
    base_prompt: str,
    text: str,
    language: Literal["zh", "en"],
) -> str:
    """Inject text placement instructions into the prompt."""
    # 验证文本非空
    text = text.strip()
    if not text:
        # 如果没有文本，返回原始 prompt 或空字符串
        return base_prompt
    
    template = self.TEXT_PLACEMENT_TEMPLATES.get(
        language, 
        self.TEXT_PLACEMENT_TEMPLATES["en"]
    )
    text_instruction = template.format(text=text)
    
    if base_prompt:
        return f"{base_prompt}, {text_instruction}"
    return text_instruction
```

### 预期收益
- 防止生成无效 prompt
- 提前失败，节省资源

---

## 问题 5: 可测试性改进建议

### 位置
整个 `PromptBuilder` 类

### 为什么是问题
- 模板字符串硬编码在类中，测试时难以 mock
- 如果需要 A/B 测试不同的 prompt 模板，需要修改代码

### 改进建议
```python
from dataclasses import dataclass
from typing import Protocol

@dataclass
class PromptTemplates:
    """可配置的 Prompt 模板"""
    base_template: str = (
        "commercial advertising poster, professional photography, "
        "high quality, studio lighting, product showcase"
    )
    zh_text_template: str = '中文文字 "{text}" 清晰渲染，文字排版美观，避免遮挡主体'
    en_text_template: str = 'English text "{text}" clearly rendered, beautiful typography, avoid obscuring main subject'


class PromptBuilder:
    """Builds prompts for Z-Image-Turbo model."""
    
    def __init__(self, templates: PromptTemplates | None = None):
        self.templates = templates or PromptTemplates()
    
    @property
    def BASE_PROMPT_TEMPLATE(self) -> str:
        return self.templates.base_template
    
    @property
    def TEXT_PLACEMENT_TEMPLATES(self) -> dict[str, str]:
        return {
            "zh": self.templates.zh_text_template,
            "en": self.templates.en_text_template,
        }
```

### 预期收益
- 支持依赖注入，便于测试
- 支持运行时配置不同模板
- 便于 A/B 测试

---

## 总结

| 优先级 | 问题 | 状态 |
|--------|------|------|
| ~~🔴 高~~ | ~~导入路径错误~~ | ✅ 已修复 |
| 🟡 中 | 缺少输入验证 | 待处理 |
| 🟡 中 | apply_modifiers 空值保护 | 待处理 |
| 🟢 低 | 魔法字符串 | 待处理 |
| 🟢 低 | 可测试性 | 待处理 |

**更新**: 导入路径问题已修复。剩余问题可在后续迭代中逐步改进。
