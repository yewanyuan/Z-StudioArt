/**
 * AuthStore 单元测试
 * 测试认证状态管理的核心功能
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from './authStore';
import type { User } from '../types';

// 测试用户数据
const mockUser: User = {
  id: 'user-123',
  phone: '13800138000',
  email: null,
  membership_tier: 'basic',
  membership_expiry: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30天后
  created_at: new Date().toISOString(),
};

const mockFreeUser: User = {
  id: 'user-456',
  phone: null,
  email: 'test@example.com',
  membership_tier: 'free',
  membership_expiry: null,
  created_at: new Date().toISOString(),
};

const mockExpiredUser: User = {
  id: 'user-789',
  phone: '13900139000',
  email: null,
  membership_tier: 'professional',
  membership_expiry: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1天前
  created_at: new Date().toISOString(),
};

describe('AuthStore', () => {
  beforeEach(() => {
    // 重置 store 状态
    useAuthStore.getState().clearAuth();
  });

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const state = useAuthStore.getState();
      
      expect(state.user).toBeNull();
      expect(state.accessToken).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
    });
  });

  describe('setAuth', () => {
    it('应该正确设置认证信息', () => {
      const { setAuth } = useAuthStore.getState();
      
      setAuth(mockUser, 'access-token-123', 'refresh-token-456');
      
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.accessToken).toBe('access-token-123');
      expect(state.refreshToken).toBe('refresh-token-456');
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
    });
  });

  describe('updateTokens', () => {
    it('应该正确更新 Token', () => {
      const { setAuth, updateTokens } = useAuthStore.getState();
      
      setAuth(mockUser, 'old-access', 'old-refresh');
      updateTokens('new-access', 'new-refresh');
      
      const state = useAuthStore.getState();
      expect(state.accessToken).toBe('new-access');
      expect(state.refreshToken).toBe('new-refresh');
      // 用户信息应该保持不变
      expect(state.user).toEqual(mockUser);
    });
  });

  describe('updateUser', () => {
    it('应该正确更新用户信息', () => {
      const { setAuth, updateUser } = useAuthStore.getState();
      
      setAuth(mockUser, 'access', 'refresh');
      updateUser({ membership_tier: 'professional' });
      
      const state = useAuthStore.getState();
      expect(state.user?.membership_tier).toBe('professional');
      expect(state.user?.id).toBe(mockUser.id);
    });

    it('用户为空时不应该更新', () => {
      const { updateUser } = useAuthStore.getState();
      
      updateUser({ membership_tier: 'professional' });
      
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
    });
  });

  describe('clearAuth', () => {
    it('应该清除所有认证状态', () => {
      const { setAuth, clearAuth } = useAuthStore.getState();
      
      setAuth(mockUser, 'access', 'refresh');
      clearAuth();
      
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.accessToken).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('setLoading', () => {
    it('应该正确设置加载状态', () => {
      const { setLoading } = useAuthStore.getState();
      
      setLoading(true);
      expect(useAuthStore.getState().isLoading).toBe(true);
      
      setLoading(false);
      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('getMembershipTier', () => {
    it('未登录时应该返回 free', () => {
      const { getMembershipTier } = useAuthStore.getState();
      expect(getMembershipTier()).toBe('free');
    });

    it('登录用户应该返回正确的会员等级', () => {
      const { setAuth, getMembershipTier } = useAuthStore.getState();
      
      setAuth(mockUser, 'access', 'refresh');
      expect(getMembershipTier()).toBe('basic');
    });

    it('会员过期时应该返回 free', () => {
      const { setAuth, getMembershipTier } = useAuthStore.getState();
      
      setAuth(mockExpiredUser, 'access', 'refresh');
      expect(getMembershipTier()).toBe('free');
    });

    it('免费用户应该返回 free', () => {
      const { setAuth, getMembershipTier } = useAuthStore.getState();
      
      setAuth(mockFreeUser, 'access', 'refresh');
      expect(getMembershipTier()).toBe('free');
    });
  });

  describe('isMembershipExpired', () => {
    it('未登录时应该返回 false', () => {
      const { isMembershipExpired } = useAuthStore.getState();
      expect(isMembershipExpired()).toBe(false);
    });

    it('没有过期时间时应该返回 false', () => {
      const { setAuth, isMembershipExpired } = useAuthStore.getState();
      
      setAuth(mockFreeUser, 'access', 'refresh');
      expect(isMembershipExpired()).toBe(false);
    });

    it('未过期时应该返回 false', () => {
      const { setAuth, isMembershipExpired } = useAuthStore.getState();
      
      setAuth(mockUser, 'access', 'refresh');
      expect(isMembershipExpired()).toBe(false);
    });

    it('已过期时应该返回 true', () => {
      const { setAuth, isMembershipExpired } = useAuthStore.getState();
      
      setAuth(mockExpiredUser, 'access', 'refresh');
      expect(isMembershipExpired()).toBe(true);
    });
  });
});
