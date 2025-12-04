/**
 * PopGraph API 服务
 * 封装与后端的 HTTP 通信
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';
import type {
  PosterGenerationRequest,
  PosterGenerationResponse,
  SceneFusionRequest,
  SceneFusionResponse,
  Template,
  TemplateCategory,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  private client: AxiosInstance;
  private userId: string = 'demo-user';
  private userTier: string = 'professional';  // 改为专业会员以测试场景融合

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 180000, // 3 minutes for batch image generation
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': this.userId,
        'X-User-Tier': this.userTier,
      },
    });
  }

  /**
   * 设置用户信息
   */
  setUser(userId: string, tier: 'free' | 'basic' | 'professional' = 'basic') {
    this.userId = userId;
    this.userTier = tier;
    this.client.defaults.headers['X-User-Id'] = userId;
    this.client.defaults.headers['X-User-Tier'] = tier;
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
}

export const apiService = new ApiService();
export default apiService;
