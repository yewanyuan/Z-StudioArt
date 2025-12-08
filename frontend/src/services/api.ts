/**
 * PopGraph API 服务
 * 封装与后端的 HTTP 通信
 * Requirements: 2.5, 10.2
 */

import axios from 'axios';
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  PosterGenerationRequest,
  PosterGenerationResponse,
  SceneFusionRequest,
  SceneFusionResponse,
  Template,
  TemplateCategory,
  SendCodeRequest,
  PhoneLoginRequest,
  PhoneRegisterRequest,
  EmailLoginRequest,
  EmailRegisterRequest,
  TokenResponse,
  UserResponse,
  AuthResponse,
  MembershipTier,
  HistoryListResponse,
  HistoryDetailResponse,
  DeleteHistoryResponse,
  PlansListResponse,
  CreateOrderRequest,
  OrderResponse,
  OrderStatusResponse,
} from '../types';
import { useAuthStore } from '../stores/authStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 是否正在刷新 Token
let isRefreshing = false;
// 等待刷新的请求队列
let refreshSubscribers: ((token: string) => void)[] = [];

// 通知所有等待的请求
const onRefreshed = (token: string) => {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
};

// 添加请求到等待队列
const addRefreshSubscriber = (callback: (token: string) => void) => {
  refreshSubscribers.push(callback);
};

class ApiService {
  private client: AxiosInstance;
  private authClient: AxiosInstance; // 用于认证相关请求，不带拦截器
  private userId: string = 'demo-user';
  private userTier: string = 'professional';

  constructor() {
    // 主客户端，带 Token 自动刷新拦截器
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 180000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 认证客户端，不带拦截器，避免循环
    this.authClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * 设置请求和响应拦截器
   */
  private setupInterceptors() {
    // 请求拦截器：添加 Authorization header
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const { accessToken, user } = useAuthStore.getState();
        
        if (accessToken) {
          config.headers.Authorization = `Bearer ${accessToken}`;
        }
        
        // 兼容旧的 X-User-Id 和 X-User-Tier headers
        if (user) {
          config.headers['X-User-Id'] = user.id;
          config.headers['X-User-Tier'] = user.membership_tier;
        } else {
          config.headers['X-User-Id'] = this.userId;
          config.headers['X-User-Tier'] = this.userTier;
        }
        
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器：处理 401 错误，自动刷新 Token
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
        
        // 如果是 401 错误且不是重试请求
        if (error.response?.status === 401 && !originalRequest._retry) {
          const { refreshToken } = useAuthStore.getState();
          
          // 没有 refresh token，直接登出
          if (!refreshToken) {
            useAuthStore.getState().clearAuth();
            return Promise.reject(error);
          }

          // 如果正在刷新，将请求加入队列
          if (isRefreshing) {
            return new Promise((resolve) => {
              addRefreshSubscriber((token: string) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                resolve(this.client(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          isRefreshing = true;

          try {
            // 尝试刷新 Token
            const response = await this.authClient.post<TokenResponse>(
              '/api/auth/refresh',
              { refresh_token: refreshToken }
            );
            
            const { access_token, refresh_token } = response.data;
            
            // 更新 store 中的 Token
            useAuthStore.getState().updateTokens(access_token, refresh_token);
            
            // 通知所有等待的请求
            onRefreshed(access_token);
            
            // 重试原始请求
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // 刷新失败，清除认证状态
            useAuthStore.getState().clearAuth();
            refreshSubscribers = [];
            return Promise.reject(refreshError);
          } finally {
            isRefreshing = false;
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  /**
   * 设置用户信息（兼容旧代码）
   */
  setUser(userId: string, tier: MembershipTier = 'basic') {
    this.userId = userId;
    this.userTier = tier;
  }

  // ============================================================================
  // 认证相关 API
  // ============================================================================

  /**
   * 发送验证码
   * Requirements: 1.6
   */
  async sendVerificationCode(phone: string): Promise<{ message: string }> {
    const response = await this.authClient.post<{ message: string }>(
      '/api/auth/send-code',
      { phone } as SendCodeRequest
    );
    return response.data;
  }

  /**
   * 手机号注册
   * Requirements: 1.1
   */
  async registerWithPhone(phone: string, code: string): Promise<AuthResponse> {
    const response = await this.authClient.post<AuthResponse>(
      '/api/auth/register/phone',
      { phone, code } as PhoneRegisterRequest
    );
    return response.data;
  }

  /**
   * 邮箱注册
   * Requirements: 1.7
   */
  async registerWithEmail(email: string, password: string): Promise<AuthResponse> {
    const response = await this.authClient.post<AuthResponse>(
      '/api/auth/register/email',
      { email, password } as EmailRegisterRequest
    );
    return response.data;
  }

  /**
   * 手机号登录
   * Requirements: 2.1
   */
  async loginWithPhone(phone: string, code: string): Promise<AuthResponse> {
    const response = await this.authClient.post<AuthResponse>(
      '/api/auth/login/phone',
      { phone, code } as PhoneLoginRequest
    );
    return response.data;
  }

  /**
   * 邮箱登录
   * Requirements: 2.6
   */
  async loginWithEmail(email: string, password: string): Promise<AuthResponse> {
    const response = await this.authClient.post<AuthResponse>(
      '/api/auth/login/email',
      { email, password } as EmailLoginRequest
    );
    return response.data;
  }

  /**
   * 刷新 Token
   * Requirements: 2.3
   */
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await this.authClient.post<TokenResponse>(
      '/api/auth/refresh',
      { refresh_token: refreshToken }
    );
    return response.data;
  }

  /**
   * 登出
   * Requirements: 3.1
   */
  async logout(refreshToken: string): Promise<{ message: string }> {
    const response = await this.authClient.post<{ message: string }>(
      '/api/auth/logout',
      { refresh_token: refreshToken }
    );
    return response.data;
  }

  /**
   * 获取当前用户信息
   * Requirements: 2.5
   */
  async getCurrentUser(): Promise<UserResponse> {
    const response = await this.client.get<UserResponse>('/api/auth/me');
    return response.data;
  }

  /**
   * 生成海报
   * Requirements: 1.1, 1.2, 2.1, 2.2
   */
  async generatePoster(request: PosterGenerationRequest): Promise<PosterGenerationResponse> {
    const response = await this.client.post<PosterGenerationResponse>(
      '/api/poster/generate',
      request
    );
    return response.data;
  }

  /**
   * 获取模板列表
   * Requirements: 3.1, 3.2, 3.3
   */
  async getTemplates(category?: TemplateCategory): Promise<Template[]> {
    const params = category ? { category } : {};
    const response = await this.client.get<Template[]>('/api/templates', { params });
    return response.data;
  }

  /**
   * 场景融合
   * Requirements: 4.1, 4.2, 4.3
   */
  async sceneFusion(request: SceneFusionRequest): Promise<SceneFusionResponse> {
    const response = await this.client.post<SceneFusionResponse>(
      '/api/scene-fusion',
      request
    );
    return response.data;
  }

  /**
   * 上传商品图片
   */
  async uploadProductImage(file: File): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.client.post<{ url: string }>(
      '/api/upload/product',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  // ============================================================================
  // 历史记录 API (Requirements: 6.1, 6.3, 6.4, 9.1)
  // ============================================================================

  /**
   * 获取历史记录列表
   * Requirements: 6.1, 9.1
   */
  async getHistory(page: number = 1, pageSize: number = 20): Promise<HistoryListResponse> {
    const response = await this.client.get<HistoryListResponse>('/api/history', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  /**
   * 获取历史记录详情
   * Requirements: 6.3
   */
  async getHistoryDetail(recordId: string): Promise<HistoryDetailResponse> {
    const response = await this.client.get<HistoryDetailResponse>(`/api/history/${recordId}`);
    return response.data;
  }

  /**
   * 删除历史记录
   * Requirements: 6.4
   */
  async deleteHistory(recordId: string): Promise<DeleteHistoryResponse> {
    const response = await this.client.delete<DeleteHistoryResponse>(`/api/history/${recordId}`);
    return response.data;
  }

  // ============================================================================
  // 支付订阅 API (Requirements: 4.1, 4.9)
  // ============================================================================

  /**
   * 获取订阅计划列表
   * Requirements: 4.1
   */
  async getPlans(): Promise<PlansListResponse> {
    const response = await this.client.get<PlansListResponse>('/api/payment/plans');
    return response.data;
  }

  /**
   * 创建支付订单
   * Requirements: 4.1
   */
  async createOrder(request: CreateOrderRequest): Promise<OrderResponse> {
    const response = await this.client.post<OrderResponse>('/api/payment/create-order', request);
    return response.data;
  }

  /**
   * 查询订单状态
   * Requirements: 4.9
   */
  async getOrderStatus(orderId: string): Promise<OrderStatusResponse> {
    const response = await this.client.get<OrderStatusResponse>(`/api/payment/order/${orderId}`);
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService;
