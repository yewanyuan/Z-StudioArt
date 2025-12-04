# Requirements Document

## Introduction

PopGraph（爆款图）是一款专为中小微电商卖家和自媒体创作者设计的"图文一体化"AI 生成工具。产品核心定位是"一键生成带正确商业文案的营销物料"，利用 Z-Image-Turbo 的中英双语文本渲染能力和亚秒级推理速度，解决用户"还要去 P 字"和"摄影贵、模特贵"的痛点。

## Glossary

- **PopGraph System**: 爆款图 SaaS 平台的核心系统，负责处理用户请求、调用 AI 模型、生成图像
- **Z-Image-Turbo**: 底层 AI 图像生成模型，具备中英双语文本渲染和亚秒级推理能力
- **Poster**: 包含图像和文字的商业营销海报
- **Template**: 预设的 Prompt 模板，封装特定风格和排版参数
- **Product Image**: 用户上传的商品白底图
- **Scene Fusion**: 将商品图与新背景场景融合的图像处理技术
- **Watermark**: 免费版生成图像上的品牌水印标识

## Requirements

### Requirement 1: 智能文案海报生成

**User Story:** As a 私域微商, I want to 输入画面描述和指定文案一键生成商业海报, so that 我可以快速制作朋友圈营销图片而无需手动 P 图。

#### Acceptance Criteria

1. WHEN a user submits a scene description and marketing text in Chinese THEN the PopGraph System SHALL generate a poster with the exact Chinese text rendered correctly without garbled characters or deformation
2. WHEN a user submits a scene description and marketing text in English THEN the PopGraph System SHALL generate a poster with the exact English text rendered correctly without garbled characters or deformation
3. WHEN the PopGraph System generates a poster containing human faces THEN the PopGraph System SHALL ensure facial features appear natural without distortion
4. WHEN the PopGraph System positions text on a poster THEN the PopGraph System SHALL automatically arrange text layout to avoid obscuring the main subject
5. WHEN a user requests poster generation THEN the PopGraph System SHALL produce output in commercial advertising style with professional visual quality

### Requirement 2: 极速生成模式

**User Story:** As a 自媒体博主, I want to 在极短时间内获得生成结果, so that 我可以快速迭代创意并提高工作效率。

#### Acceptance Criteria

1. WHEN a user initiates a single poster generation request THEN the PopGraph System SHALL return the result within 5 seconds on standard hardware
2. WHEN a user selects the preview mode THEN the PopGraph System SHALL generate 4 variant posters in a single batch for user selection
3. WHILE the PopGraph System processes generation requests THEN the PopGraph System SHALL maintain API success rate above 99 percent

### Requirement 3: 预设商业模板

**User Story:** As a 淘宝小店主, I want to 使用预设的商业模板而无需编写复杂提示词, so that 我可以轻松生成专业风格的营销图片。

#### Acceptance Criteria

1. WHEN a user selects a promotional template THEN the PopGraph System SHALL apply red background, explosion sticker style, and large font size parameters
2. WHEN a user selects a premium template THEN the PopGraph System SHALL apply minimalist whitespace, studio lighting, and black-gold color scheme parameters
3. WHEN a user selects a holiday template THEN the PopGraph System SHALL inject corresponding festival elements based on the selected holiday type (Spring Festival, Valentine's Day, Double Eleven)
4. WHEN a user applies any template THEN the PopGraph System SHALL combine template parameters with user-provided text to generate the final poster

### Requirement 4: 商品图场景融合

**User Story:** As a 电商运营, I want to 上传商品白底图并自动生成不同场景背景, so that 我可以低成本批量生产商品场景图而无需请摄影师。

#### Acceptance Criteria

1. WHEN a user uploads a product image with white background THEN the PopGraph System SHALL extract and preserve the product subject accurately
2. WHEN a user specifies a target scene description THEN the PopGraph System SHALL generate a new background matching the description while maintaining the original product appearance
3. WHEN the PopGraph System performs scene fusion THEN the PopGraph System SHALL ensure seamless integration between product and background with consistent lighting and perspective

### Requirement 5: 尺寸自适应

**User Story:** As a 内容创作者, I want to 一键切换输出图片尺寸, so that 我可以为不同平台生成适配的图片规格。

#### Acceptance Criteria

1. WHEN a user selects square format THEN the PopGraph System SHALL generate output in 1:1 aspect ratio suitable for WeChat Moments
2. WHEN a user selects mobile poster format THEN the PopGraph System SHALL generate output in 9:16 aspect ratio suitable for phone screens
3. WHEN a user selects video cover format THEN the PopGraph System SHALL generate output in 16:9 aspect ratio suitable for video thumbnails
4. WHEN a user switches output size THEN the PopGraph System SHALL automatically adjust layout and text positioning to fit the new dimensions

### Requirement 6: 内容安全与合规

**User Story:** As a 平台运营者, I want to 系统自动过滤敏感内容, so that 生成的内容符合法规要求并保护平台声誉。

#### Acceptance Criteria

1. WHEN a user submits input containing sensitive keywords THEN the PopGraph System SHALL reject the request and display an appropriate warning message
2. WHEN the PopGraph System generates text content THEN the PopGraph System SHALL maintain typo rate below 10 percent for the specified text

### Requirement 7: 会员与水印系统

**User Story:** As a 产品运营, I want to 通过分层会员体系和水印机制实现商业化, so that 产品可以持续运营并实现盈利。

#### Acceptance Criteria

1. WHEN a free-tier user generates a poster THEN the PopGraph System SHALL add a visible watermark to the output image
2. WHEN a free-tier user exceeds 5 daily generations THEN the PopGraph System SHALL block further generation requests until the next day
3. WHEN a basic member generates a poster THEN the PopGraph System SHALL produce output without watermark and with priority processing
4. WHEN a professional member requests scene fusion feature THEN the PopGraph System SHALL grant access to the product visualization functionality
