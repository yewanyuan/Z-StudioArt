/**
 * 认证状态管理 Store
 * 使用 Zustand 管理用户认证状态
 * Requirements: 10.1, 10.2
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User, MembershipTier } from '../types';

interface AuthState {
  // 用户信息
  user: User | null;
  // Token
  accessToken: string | null;
  refreshToken: string | null;
  // 状态标志
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
}

interface AuthActions {
  // 设置用户和 Token
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  // 更新 Token
  updateTokens: (accessToken: string, refreshToken: string) => void;
  // 更新用户信息
  updateUser: (user: Partial<User>) => void;
  // 清除认证状态（登出）
  clearAuth: () => void;
  // 设置加载状态
  setLoading: (loading: boolean) => void;
  // 初始化完成
  setInitialized: () => void;
  // 获取当前会员等级
  getMembershipTier: () => MembershipTier;
  // 检查会员是否过期
  isMembershipExpired: () => boolean;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // 初始状态
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      isInitialized: false,

      // 设置认证信息
      setAuth: (user, accessToken, refreshToken) => {
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      // 更新 Token
      updateTokens: (accessToken, refreshToken) => {
        set({
          accessToken,
          refreshToken,
        });
      },

      // 更新用户信息
      updateUser: (userData) => {
        const currentUser = get().user;
        if (currentUser) {
          set({
            user: { ...currentUser, ...userData },
          });
        }
      },

      // 清除认证状态
      clearAuth: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },

      // 设置加载状态
      setLoading: (loading) => {
        set({ isLoading: loading });
      },

      // 设置初始化完成
      setInitialized: () => {
        set({ isInitialized: true });
      },

      // 获取会员等级
      getMembershipTier: () => {
        const user = get().user;
        if (!user) return 'free';
        
        // 检查会员是否过期
        if (get().isMembershipExpired()) {
          return 'free';
        }
        
        return user.membership_tier;
      },

      // 检查会员是否过期
      isMembershipExpired: () => {
        const user = get().user;
        if (!user || !user.membership_expiry) return false;
        
        const expiryDate = new Date(user.membership_expiry);
        return expiryDate < new Date();
      },
    }),
    {
      name: 'popgraph-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// 导出便捷的选择器 hooks
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useIsAuthLoading = () => useAuthStore((state) => state.isLoading);
export const useAccessToken = () => useAuthStore((state) => state.accessToken);
export const useRefreshToken = () => useAuthStore((state) => state.refreshToken);
