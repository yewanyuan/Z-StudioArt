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

// ============================================================================
// Auth Types
// ============================================================================

export interface User {
  id: string;
  phone?: string;
  email?: string;
  membership_tier: MembershipTier;
  membership_expiry?: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Auth API Request/Response Types
export interface SendCodeRequest {
  phone: string;
}

export interface PhoneLoginRequest {
  phone: string;
  code: string;
}

export interface PhoneRegisterRequest {
  phone: string;
  code: string;
}

export interface EmailLoginRequest {
  email: string;
  password: string;
}

export interface EmailRegisterRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  phone?: string;
  email?: string;
  membership_tier: MembershipTier;
  membership_expiry?: string;
}

export interface AuthResponse {
  user: UserResponse;
  tokens: TokenResponse;
}

// ============================================================================
// History Types (Requirements: 6.1, 6.3, 6.4, 9.1)
// ============================================================================

export type GenerationType = 'poster' | 'scene_fusion';

export interface HistoryItem {
  id: string;
  type: GenerationType;
  thumbnail_url: string | null;
  created_at: string;
  input_params: Record<string, unknown>;
  output_urls: string[];
  processing_time_ms: number;
  has_watermark: boolean;
}

export interface HistoryListResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface HistoryDetailResponse {
  id: string;
  type: GenerationType;
  created_at: string;
  input_params: Record<string, unknown>;
  output_urls: string[];
  processing_time_ms: number;
  has_watermark: boolean;
}

export interface DeleteHistoryResponse {
  success: boolean;
  message: string;
}

// ============================================================================
// Payment Types (Requirements: 4.1, 4.9)
// ============================================================================

export type PaymentMethod = 'alipay' | 'wechat' | 'unionpay';

export type PaymentStatus = 'pending' | 'paid' | 'failed' | 'expired' | 'refunded';

export type SubscriptionPlan = 'basic_monthly' | 'basic_yearly' | 'pro_monthly' | 'pro_yearly';

export interface PlanResponse {
  plan: SubscriptionPlan;
  name: string;
  price: number;
  price_display: string;
  tier: MembershipTier;
  duration_days: number;
  description: string;
}

export interface PlansListResponse {
  plans: PlanResponse[];
}

export interface CreateOrderRequest {
  plan: SubscriptionPlan;
  method: PaymentMethod;
}

export interface OrderResponse {
  order_id: string;
  user_id: string;
  plan: SubscriptionPlan;
  method: PaymentMethod;
  amount: number;
  amount_display: string;
  status: PaymentStatus;
  payment_url: string | null;
  qrcode_content: string | null;
  created_at: string;
  expires_in_seconds: number;
}

export interface OrderStatusResponse {
  order_id: string;
  status: PaymentStatus;
  paid_at: string | null;
}
