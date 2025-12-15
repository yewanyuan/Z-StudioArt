/**
 * PopGraph 应用主组件
 * Based on Mathilda Art Gallery Template
 * 集成路由和认证状态管理
 */

import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute, PublicRoute } from './components/ProtectedRoute';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { HomePage, AboutPage, LoginPage, RegisterPage, HistoryPage, SubscriptionPage } from './pages';
import { PosterGeneratorPage } from './components/PosterGeneratorPage';
import { SceneFusionPage } from './components/SceneFusionPage';
import { useAuthStore } from './stores/authStore';
import { apiService } from './services/api';

/**
 * 应用初始化组件 - 处理认证状态恢复
 */
function AppInitializer({ children }: { children: React.ReactNode }) {
  const { refreshToken, setAuth, clearAuth, setInitialized, isInitialized } = useAuthStore();

  useEffect(() => {
    const initAuth = async () => {
      // 如果有 refresh token，尝试恢复会话
      if (refreshToken) {
        try {
          const tokenResponse = await apiService.refreshToken(refreshToken);
          const userResponse = await apiService.getCurrentUser();
          setAuth(userResponse, tokenResponse.access_token, tokenResponse.refresh_token);
        } catch (err) {
          console.error('Session restore failed:', err);
          clearAuth();
        }
      }
      setInitialized();
    };

    if (!isInitialized) {
      initAuth();
    }
  }, [refreshToken, setAuth, clearAuth, setInitialized, isInitialized]);

  // 显示加载状态 - 使用模板风格的加载器
  if (!isInitialized) {
    return (
      <div className="page-loader">
        <div className="loader-spinner" />
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * 应用根组件
 * 使用 ErrorBoundary 包装整个应用以捕获错误
 */
function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AppInitializer>
          <Routes>
            {/* 公开路由 - 首页 */}
            <Route path="/" element={<HomePage />} />

            {/* 公开路由 - 关于页 */}
            <Route path="/about" element={<AboutPage />} />

            {/* 公开路由 - 登录页 */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              }
            />

            {/* 公开路由 - 注册页 */}
            <Route
              path="/register"
              element={
                <PublicRoute>
                  <RegisterPage />
                </PublicRoute>
              }
            />

            {/* 受保护路由 - 海报生成页 */}
            <Route
              path="/create"
              element={
                <ProtectedRoute>
                  <PosterGeneratorPage />
                </ProtectedRoute>
              }
            />

            {/* 受保护路由 - 场景融合页 */}
            <Route
              path="/scene-fusion"
              element={
                <ProtectedRoute>
                  <SceneFusionPage />
                </ProtectedRoute>
              }
            />

            {/* 受保护/公开路由 - 作品展示页 (Gallery) */}
            <Route path="/gallery" element={<HistoryPage />} />

            {/* 公开路由 - 订阅页面 */}
            <Route path="/subscription" element={<SubscriptionPage />} />

            {/* 其他路由重定向到首页 */}
            <Route path="*" element={<HomePage />} />
          </Routes>
        </AppInitializer>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
