/**
 * 订阅页面
 * Requirements: 4.1, 4.8
 * 
 * 功能：
 * - 显示订阅计划列表
 * - 显示当前会员状态
 * - 选择计划并发起支付
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { useAuthStore } from '../stores/authStore';
import type { PlanResponse } from '../types';
import { PaymentModal } from '../components';

export function SubscriptionPage() {
  const navigate = useNavigate();
  const { user, clearAuth, refreshToken, updateUser } = useAuthStore();
  
  // 计划列表状态
  const [plans, setPlans] = useState<PlanResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // 支付模态框状态
  const [selectedPlan, setSelectedPlan] = useState<PlanResponse | null>(null);
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);

  /**
   * 加载订阅计划
   */
  useEffect(() => {
    const loadPlans = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await apiService.getPlans();
        setPlans(response.plans);
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : '加载订阅计划失败';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadPlans();
  }, []);

  /**
   * 选择计划
   */
  const handleSelectPlan = (plan: PlanResponse) => {
    setSelectedPlan(plan);
    setIsPaymentModalOpen(true);
  };

  /**
   * 关闭支付模态框
   */
  const handleClosePaymentModal = () => {
    setIsPaymentModalOpen(false);
    setSelectedPlan(null);
  };

  /**
   * 支付成功回调
   */
  const handlePaymentSuccess = async () => {
    // 刷新用户信息
    try {
      const userInfo = await apiService.getCurrentUser();
      updateUser(userInfo);
    } catch (err) {
      console.error('Failed to refresh user info:', err);
    }
    
    handleClosePaymentModal();
  };

  /**
   * 登出
   */
  const handleLogout = async () => {
    try {
      if (refreshToken) {
        await apiService.logout(refreshToken);
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      clearAuth();
      navigate('/login');
    }
  };

  /**
   * 格式化会员过期时间
   */
  const formatExpiryDate = (dateStr?: string) => {
    if (!dateStr) return '无';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  /**
   * 获取会员等级显示名称
   */
  const getTierDisplayName = (tier: string) => {
    switch (tier) {
      case 'professional':
        return '专业版';
      case 'basic':
        return '基础版';
      default:
        return '免费版';
    }
  };

  /**
   * 获取会员等级样式
   */
  const getTierStyle = (tier: string) => {
    switch (tier) {
      case 'professional':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'basic':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  /**
   * 检查计划是否为当前计划
   */
  const isCurrentPlan = (plan: PlanResponse) => {
    if (!user) return false;
    return user.membership_tier === plan.tier;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      {/* 顶部导航栏 */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-900/95 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* 左侧：返回和标题 */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="p-2 text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-xl font-semibold text-white">会员订阅</h1>
            </div>

            {/* 右侧：用户信息 */}
            {user && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-300">
                  {user.phone || user.email}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${getTierStyle(user.membership_tier)}`}>
                  {getTierDisplayName(user.membership_tier)}
                </span>
                <button
                  onClick={() => navigate('/history')}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                  title="生成历史"
                >
                  📜
                </button>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                  title="退出登录"
                >
                  退出
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="pt-20 pb-8 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
        {/* 当前会员状态卡片 */}
        {user && (
          <MembershipStatusCard
            user={user}
            getTierDisplayName={getTierDisplayName}
            getTierStyle={getTierStyle}
            formatExpiryDate={formatExpiryDate}
          />
        )}

        {/* 错误提示 */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-4 text-red-300 hover:text-red-200"
            >
              关闭
            </button>
          </div>
        )}

        {/* 加载状态 */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-4">
              <div className="animate-spin rounded-full h-12 w-12 border-2 border-indigo-500/30 border-t-indigo-500" />
              <span className="text-gray-400">加载订阅计划...</span>
            </div>
          </div>
        )}

        {/* 订阅计划列表 */}
        {!isLoading && plans.length > 0 && (
          <div className="mt-8">
            <h2 className="text-lg font-medium text-white mb-6">选择订阅计划</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {plans.map((plan) => (
                <PlanCard
                  key={plan.plan}
                  plan={plan}
                  isCurrentPlan={isCurrentPlan(plan)}
                  onSelect={() => handleSelectPlan(plan)}
                />
              ))}
            </div>
          </div>
        )}

        {/* 功能对比表 */}
        {!isLoading && plans.length > 0 && (
          <FeatureComparisonTable />
        )}
      </main>

      {/* 支付模态框 */}
      {selectedPlan && (
        <PaymentModal
          isOpen={isPaymentModalOpen}
          plan={selectedPlan}
          onClose={handleClosePaymentModal}
          onSuccess={handlePaymentSuccess}
        />
      )}
    </div>
  );
}


/**
 * 会员状态卡片组件
 */
interface MembershipStatusCardProps {
  user: {
    membership_tier: string;
    membership_expiry?: string;
  };
  getTierDisplayName: (tier: string) => string;
  getTierStyle: (tier: string) => string;
  formatExpiryDate: (date?: string) => string;
}

function MembershipStatusCard({ 
  user, 
  getTierDisplayName, 
  getTierStyle, 
  formatExpiryDate 
}: MembershipStatusCardProps) {
  const isExpired = user.membership_expiry 
    ? new Date(user.membership_expiry) < new Date() 
    : false;

  return (
    <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-6">
      <h2 className="text-lg font-medium text-white mb-4">当前会员状态</h2>
      <div className="flex items-center gap-4">
        <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
          user.membership_tier === 'professional' 
            ? 'bg-purple-500/20' 
            : user.membership_tier === 'basic'
            ? 'bg-blue-500/20'
            : 'bg-gray-500/20'
        }`}>
          {user.membership_tier === 'professional' ? (
            <svg className="w-8 h-8 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          ) : user.membership_tier === 'basic' ? (
            <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
            </svg>
          ) : (
            <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          )}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className={`text-sm px-2 py-0.5 rounded-full border ${getTierStyle(user.membership_tier)}`}>
              {getTierDisplayName(user.membership_tier)}
            </span>
            {isExpired && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/30">
                已过期
              </span>
            )}
          </div>
          {user.membership_tier !== 'free' && (
            <p className="mt-2 text-sm text-gray-400">
              {isExpired ? '过期时间' : '有效期至'}：{formatExpiryDate(user.membership_expiry)}
            </p>
          )}
          {user.membership_tier === 'free' && (
            <p className="mt-2 text-sm text-gray-400">
              升级会员享受更多权益
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * 计划卡片组件
 */
interface PlanCardProps {
  plan: PlanResponse;
  isCurrentPlan: boolean;
  onSelect: () => void;
}

function PlanCard({ plan, isCurrentPlan, onSelect }: PlanCardProps) {
  const isYearly = plan.plan.includes('yearly');
  const isPro = plan.tier === 'professional';
  
  return (
    <div className={`relative bg-gray-800/50 rounded-xl border ${
      isPro 
        ? 'border-purple-500/50' 
        : 'border-gray-700'
    } p-6 flex flex-col`}>
      {/* 推荐标签 */}
      {isPro && isYearly && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="px-3 py-1 bg-purple-500 text-white text-xs font-medium rounded-full">
            最受欢迎
          </span>
        </div>
      )}
      
      {/* 计划名称 */}
      <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
      
      {/* 价格 */}
      <div className="mt-4">
        <span className="text-3xl font-bold text-white">{plan.price_display}</span>
        <span className="text-gray-400 ml-1">
          /{isYearly ? '年' : '月'}
        </span>
      </div>
      
      {/* 描述 */}
      <p className="mt-3 text-sm text-gray-400 flex-grow">
        {plan.description}
      </p>
      
      {/* 时长 */}
      <p className="mt-2 text-xs text-gray-500">
        有效期：{plan.duration_days} 天
      </p>
      
      {/* 按钮 */}
      <button
        onClick={onSelect}
        disabled={isCurrentPlan}
        className={`mt-6 w-full py-3 rounded-lg font-medium transition-colors ${
          isCurrentPlan
            ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
            : isPro
            ? 'bg-purple-600 hover:bg-purple-700 text-white'
            : 'bg-indigo-600 hover:bg-indigo-700 text-white'
        }`}
      >
        {isCurrentPlan ? '当前计划' : '选择此计划'}
      </button>
    </div>
  );
}

/**
 * 功能对比表组件
 */
function FeatureComparisonTable() {
  const features = [
    { name: '每日生成次数', free: '5 次', basic: '50 次', pro: '无限制' },
    { name: '图片分辨率', free: '标准', basic: '高清', pro: '超高清' },
    { name: '水印', free: '有', basic: '无', pro: '无' },
    { name: '历史记录保留', free: '7 天', basic: '90 天', pro: '90 天' },
    { name: '批量生成', free: '1 张', basic: '4 张', pro: '4 张' },
    { name: '优先处理', free: '否', basic: '否', pro: '是' },
    { name: '专属模板', free: '否', basic: '部分', pro: '全部' },
  ];

  return (
    <div className="mt-12">
      <h2 className="text-lg font-medium text-white mb-6">功能对比</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="py-4 px-4 text-left text-sm font-medium text-gray-400">功能</th>
              <th className="py-4 px-4 text-center text-sm font-medium text-gray-400">免费版</th>
              <th className="py-4 px-4 text-center text-sm font-medium text-blue-400">基础版</th>
              <th className="py-4 px-4 text-center text-sm font-medium text-purple-400">专业版</th>
            </tr>
          </thead>
          <tbody>
            {features.map((feature, index) => (
              <tr key={index} className="border-b border-gray-700/50">
                <td className="py-4 px-4 text-sm text-gray-300">{feature.name}</td>
                <td className="py-4 px-4 text-center text-sm text-gray-400">{feature.free}</td>
                <td className="py-4 px-4 text-center text-sm text-gray-300">{feature.basic}</td>
                <td className="py-4 px-4 text-center text-sm text-gray-300">{feature.pro}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default SubscriptionPage;
