/**
 * 路由守卫组件
 * 保护需要认证的路由，未登录用户重定向到登录页
 * Requirements: 10.3
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import type { ReactNode } from 'react';

interface ProtectedRouteProps {
  children: ReactNode;
  /** 是否需要特定会员等级 */
  requiredTier?: 'basic' | 'professional';
  /** 未授权时重定向的路径 */
  redirectTo?: string;
}

/**
 * 路由守卫组件
 * - 未登录用户重定向到登录页
 * - 可选：检查会员等级
 */
export function ProtectedRoute({
  children,
  requiredTier,
  redirectTo = '/login',
}: ProtectedRouteProps) {
  const location = useLocation();
  const { isAuthenticated, isInitialized, user } = useAuthStore();

  // 等待初始化完成
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
      </div>
    );
  }

  // 未登录，重定向到登录页
  if (!isAuthenticated) {
    // 保存当前路径，登录后可以返回
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // 检查会员等级
  if (requiredTier && user) {
    const tierOrder = { free: 0, basic: 1, professional: 2 };
    const userTierLevel = tierOrder[user.membership_tier] || 0;
    const requiredTierLevel = tierOrder[requiredTier] || 0;

    if (userTierLevel < requiredTierLevel) {
      // 会员等级不足，重定向到订阅页面
      return <Navigate to="/subscription" state={{ from: location }} replace />;
    }
  }

  return <>{children}</>;
}

/**
 * 公开路由组件
 * 已登录用户访问登录/注册页时重定向到首页
 */
interface PublicRouteProps {
  children: ReactNode;
  /** 已登录时重定向的路径 */
  redirectTo?: string;
}

export function PublicRoute({
  children,
  redirectTo = '/',
}: PublicRouteProps) {
  const location = useLocation();
  const { isAuthenticated, isInitialized } = useAuthStore();

  // 等待初始化完成
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
      </div>
    );
  }

  // 已登录，重定向到首页或之前的页面
  if (isAuthenticated) {
    const from = (location.state as { from?: Location })?.from?.pathname || redirectTo;
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
}

export default ProtectedRoute;
