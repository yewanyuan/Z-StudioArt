/**
 * PopGraph 前端类型定义
 * 与后端 schemas.py 保持一致
 */

// ============================================================================
// Enums
// ============================================================================

export type MembershipTier = 'free' | 'basic' | 'professional';

export type TemplateCategory = 'promotional' | 'premium' | 'holiday';

export type HolidayType = 'spring_festival' | 'valentines' | 'double_eleven';

export type AspectRatio = '1:1' | '9:16' | '16:9' | 'custom';

export type Language = 'zh' | 'en';

// ============================================================================
// Poster Generation Types
// ============================================================================

export interface PosterGenerationRequest {
  scene_description: string;
  marketing_text: string;
  language: Language;
  template_id?: string;
  aspect_ratio: AspectRatio;
  custom_width?: number;
  custom_height?: number;
  batch_size: 1 | 4;
}

export interface GeneratedImage {
  id: string;
  url: string;
  thumbnail_url: string;
  has_watermark: boolean;
  width: number;
  height: number;
  image_base64?: string;  // 可选的 Base64 图像数据
}

export interface PosterGenerationResponse {
  request_id: string;
  images: GeneratedImage[];
  processing_time_ms: number;
}

// ============================================================================
// Template Types
// ============================================================================

export interface PromptModifiers {
  style_keywords: string[];
  color_scheme: string;
  layout_hints: string;
  font_style: string;
}

export interface Template {
  id: string;
  name: string;
  category: TemplateCategory;
  holiday_type?: HolidayType;
  prompt_modifiers: PromptModifiers;
  preview_url: string;
}

// ============================================================================
// Scene Fusion Types
// ============================================================================

export interface SceneFusionRequest {
  product_image_url: string;
  target_scene: string;
  aspect_ratio: AspectRatio;
  custom_width?: number;
  custom_height?: number;
}

export interface SceneFusionResponse {
  request_id: string;
  fused_image_url: string;
  processing_time_ms: number;
}

// ============================================================================
// API Error Types
// ============================================================================

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface GenerationState {
  isLoading: boolean;
  error?: string;
  images: GeneratedImage[];
}
