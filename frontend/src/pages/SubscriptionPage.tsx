/**
 * 订阅页面
 * Based on Mathilda Art Gallery Template - About/Skills Style
 * Requirements: 4.1, 4.8
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';
import { useAuthStore } from '../stores/authStore';
import { useLanguageStore } from '../stores/languageStore';
import type { PlanResponse } from '../types';
import { PaymentModal } from '../components';
import { Header, Footer } from '../components/layout';

// Translations
const SUBSCRIPTION_TRANSLATIONS = {
  zh: {
    pageTitle: '订阅计划',
    pageSubtitle: '选择适合您的计划，解锁更多创作能力',
    loginPrompt: '登录后可查看当前会员状态并订阅计划',
    loginNow: '立即登录',
    loadingPlans: '加载订阅计划...',
    choosePlan: '选择订阅计划',
    currentPlan: '当前计划',
    selectPlan: '选择此计划',
    loginToSubscribe: '登录订阅',
    mostPopular: '最受欢迎',
    perYear: '年',
    perMonth: '月',
    validFor: '有效期',
    days: '天',
    memberStatus: '当前会员状态',
    expired: '已过期',
    expiryDate: '有效期至',
    expiredDate: '过期时间',
    upgradePrompt: '升级会员享受更多权益',
    featureComparison: '功能对比',
    tierNames: {
      professional: '专业版',
      basic: '基础版',
      free: '免费版',
    },
    planNames: {
      basic_monthly: '基础版月度',
      basic_yearly: '基础版年度',
      pro_monthly: '专业版月度',
      pro_yearly: '专业版年度',
    },
    planDescriptions: {
      basic_monthly: '适合个人用户，按月订阅更灵活',
      basic_yearly: '适合个人用户，年度订阅更优惠',
      pro_monthly: '适合专业创作者，解锁全部功能',
      pro_yearly: '适合专业创作者，年度订阅享最大优惠',
    },
    features: [
      { name: '每日生成次数', free: '5 次', basic: '50 次', pro: '无限制' },
      { name: '图片分辨率', free: '标准', basic: '高清', pro: '超高清' },
      { name: '水印', free: '有', basic: '无', pro: '无' },
      { name: '历史记录保留', free: '7 天', basic: '90 天', pro: '90 天' },
      { name: '批量生成', free: '1 张', basic: '4 张', pro: '4 张' },
      { name: '优先处理', free: '否', basic: '否', pro: '是' },
      { name: '专属模板', free: '否', basic: '部分', pro: '全部' },
    ],
    featureTableHeaders: { feature: '功能', free: '免费版', basic: '基础版', pro: '专业版' },
  },
  en: {
    pageTitle: 'Subscription Plans',
    pageSubtitle: 'Choose the right plan for you and unlock more creative capabilities',
    loginPrompt: 'Log in to view your membership status and subscribe to plans',
    loginNow: 'Log In',
    loadingPlans: 'Loading subscription plans...',
    choosePlan: 'Choose a Plan',
    currentPlan: 'Current Plan',
    selectPlan: 'Select Plan',
    loginToSubscribe: 'Log in to Subscribe',
    mostPopular: 'Most Popular',
    perYear: 'year',
    perMonth: 'month',
    validFor: 'Valid for',
    days: 'days',
    memberStatus: 'Current Membership Status',
    expired: 'Expired',
    expiryDate: 'Valid until',
    expiredDate: 'Expired on',
    upgradePrompt: 'Upgrade to enjoy more benefits',
    featureComparison: 'Feature Comparison',
    tierNames: {
      professional: 'Professional',
      basic: 'Basic',
      free: 'Free',
    },
    planNames: {
      basic_monthly: 'Basic Monthly',
      basic_yearly: 'Basic Yearly',
      pro_monthly: 'Professional Monthly',
      pro_yearly: 'Professional Yearly',
    },
    planDescriptions: {
      basic_monthly: 'Perfect for individuals, flexible monthly subscription',
      basic_yearly: 'Perfect for individuals, save more with yearly subscription',
      pro_monthly: 'For professional creators, unlock all features',
      pro_yearly: 'For professional creators, best value with yearly subscription',
    },
    features: [
      { name: 'Daily generations', free: '5', basic: '50', pro: 'Unlimited' },
      { name: 'Image resolution', free: 'Standard', basic: 'HD', pro: 'Ultra HD' },
      { name: 'Watermark', free: 'Yes', basic: 'No', pro: 'No' },
      { name: 'History retention', free: '7 days', basic: '90 days', pro: '90 days' },
      { name: 'Batch generation', free: '1 image', basic: '4 images', pro: '4 images' },
      { name: 'Priority processing', free: 'No', basic: 'No', pro: 'Yes' },
      { name: 'Exclusive templates', free: 'No', basic: 'Partial', pro: 'All' },
    ],
    featureTableHeaders: { feature: 'Feature', free: 'Free', basic: 'Basic', pro: 'Professional' },
  },
};

export function SubscriptionPage() {
  const { user, isAuthenticated, updateUser } = useAuthStore();
  const { language } = useLanguageStore();
  const t = SUBSCRIPTION_TRANSLATIONS[language];

  const [plans, setPlans] = useState<PlanResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<PlanResponse | null>(null);
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);

  useEffect(() => {
    const loadPlans = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiService.getPlans();
        setPlans(response.plans);
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : (language === 'zh' ? '加载订阅计划失败' : 'Failed to load subscription plans');
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };
    loadPlans();
  }, [language]);

  const handleSelectPlan = (plan: PlanResponse) => {
    if (!isAuthenticated) return;
    setSelectedPlan(plan);
    setIsPaymentModalOpen(true);
  };

  const handleClosePaymentModal = () => {
    setIsPaymentModalOpen(false);
    setSelectedPlan(null);
  };

  const handlePaymentSuccess = async () => {
    try {
      const userInfo = await apiService.getCurrentUser();
      updateUser(userInfo);
    } catch (err) {
      console.error('Failed to refresh user info:', err);
    }
    handleClosePaymentModal();
  };

  const formatExpiryDate = (dateStr?: string) => {
    if (!dateStr) return language === 'zh' ? '无' : 'None';
    const date = new Date(dateStr);
    return date.toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getTierDisplayName = (tier: string) => {
    switch (tier) {
      case 'professional': return t.tierNames.professional;
      case 'basic': return t.tierNames.basic;
      default: return t.tierNames.free;
    }
  };

  const isCurrentPlan = (plan: PlanResponse) => {
    if (!user) return false;
    return user.membership_tier === plan.tier;
  };

  return (
    <div className="page-wrapper">
      <div className="bg-curve" />
      <Header />

      <section className="py-8 border-b border-[var(--border-light)]">
        <div className="container-main">
          <div className="text-center">
            <h2 className="section-title">{t.pageTitle}</h2>
            <p className="text-[var(--text-muted)] max-w-2xl mx-auto">{t.pageSubtitle}</p>
          </div>
        </div>
      </section>

      <main className="main-content">
        <div className="container-main">
          {isAuthenticated && user && (
            <MembershipStatusCard
              user={user}
              getTierDisplayName={getTierDisplayName}
              formatExpiryDate={formatExpiryDate}
              t={t}
            />
          )}

          {!isAuthenticated && (
            <div className="card mb-8 bg-[var(--primary-bg)]">
              <div className="card-body text-center">
                <p className="text-[var(--text-muted)] mb-4">{t.loginPrompt}</p>
                <Link to="/login" className="btn-primary">{t.loginNow}</Link>
              </div>
            </div>
          )}

          {error && (
            <div className="alert alert-error flex items-start gap-3 mb-6">
              <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-sm flex-1">{error}</p>
              <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}

          {isLoading && (
            <div className="flex items-center justify-center py-20">
              <div className="flex flex-col items-center gap-4">
                <div className="loader-spinner" />
                <span className="text-[var(--text-muted)]">{t.loadingPlans}</span>
              </div>
            </div>
          )}

          {!isLoading && plans.length > 0 && (
            <div className="mt-8">
              <h3 className="text-xl font-bold text-[var(--text-dark)] mb-6 text-center">{t.choosePlan}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 pt-4">
                {plans.map((plan) => (
                  <PlanCard
                    key={plan.plan}
                    plan={plan}
                    isCurrentPlan={isCurrentPlan(plan)}
                    isAuthenticated={isAuthenticated}
                    onSelect={() => handleSelectPlan(plan)}
                    t={t}
                  />
                ))}
              </div>
            </div>
          )}

          {!isLoading && plans.length > 0 && (
            <FeatureComparisonTable t={t} />
          )}
        </div>
      </main>

      <Footer />

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

interface MembershipStatusCardProps {
  user: { membership_tier: string; membership_expiry?: string };
  getTierDisplayName: (tier: string) => string;
  formatExpiryDate: (date?: string) => string;
  t: typeof SUBSCRIPTION_TRANSLATIONS.zh;
}

function MembershipStatusCard({ user, getTierDisplayName, formatExpiryDate, t }: MembershipStatusCardProps) {
  const isExpired = user.membership_expiry ? new Date(user.membership_expiry) < new Date() : false;
  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'professional': return '👑';
      case 'basic': return '⭐';
      default: return '👤';
    }
  };

  return (
    <div className="card mb-8">
      <div className="card-body">
        <h4 className="text-[var(--text-dark)] mb-4">{t.memberStatus}</h4>
        <div className="flex items-center gap-4">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl ${
            user.membership_tier === 'professional' ? 'bg-purple-100' :
            user.membership_tier === 'basic' ? 'bg-blue-100' : 'bg-[var(--primary-bg)]'
          }`}>
            {getTierIcon(user.membership_tier)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-sm px-3 py-1 rounded-full font-medium ${
                user.membership_tier === 'professional' ? 'bg-purple-100 text-purple-700' :
                user.membership_tier === 'basic' ? 'bg-blue-100 text-blue-700' :
                'bg-[var(--primary-bg)] text-[var(--primary)]'
              }`}>
                {getTierDisplayName(user.membership_tier)}
              </span>
              {isExpired && (
                <span className="text-xs px-2 py-1 rounded-full bg-red-100 text-red-600">{t.expired}</span>
              )}
            </div>
            {user.membership_tier !== 'free' && (
              <p className="mt-2 text-sm text-[var(--text-muted)]">
                {isExpired ? t.expiredDate : t.expiryDate}：{formatExpiryDate(user.membership_expiry)}
              </p>
            )}
            {user.membership_tier === 'free' && (
              <p className="mt-2 text-sm text-[var(--text-muted)]">{t.upgradePrompt}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

interface PlanCardProps {
  plan: PlanResponse;
  isCurrentPlan: boolean;
  isAuthenticated: boolean;
  onSelect: () => void;
  t: typeof SUBSCRIPTION_TRANSLATIONS.zh;
}

function PlanCard({ plan, isCurrentPlan, isAuthenticated, onSelect, t }: PlanCardProps) {
  const isYearly = plan.plan.includes('yearly');
  const isPro = plan.tier === 'professional';

  // Get translated plan name and description
  const planKey = plan.plan.replace('pro_', 'pro_') as keyof typeof t.planNames;
  const planName = t.planNames[planKey] || plan.name;
  const planDescription = t.planDescriptions[planKey] || plan.description;

  return (
    <div className={`card relative flex flex-col h-full overflow-visible ${isPro ? 'ring-2 ring-[var(--primary)]' : ''}`}>
      {isPro && isYearly && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
          <span className="px-3 py-1 bg-[var(--primary)] text-white text-xs font-bold rounded-full shadow-lg whitespace-nowrap">
            {t.mostPopular}
          </span>
        </div>
      )}
      <div className="card-body flex flex-col h-full">
        <h4 className="text-[var(--text-dark)]">{planName}</h4>
        <div className="mt-4">
          <span className="text-3xl font-bold text-[var(--primary)]">{plan.price_display}</span>
          <span className="text-[var(--text-muted)] ml-1">/{isYearly ? t.perYear : t.perMonth}</span>
        </div>
        <p className="mt-3 text-sm text-[var(--text-muted)] flex-grow">{planDescription}</p>
        <p className="mt-2 text-xs text-[var(--text-muted)]">{t.validFor}: {plan.duration_days} {t.days}</p>
        {isAuthenticated ? (
          <button
            onClick={onSelect}
            disabled={isCurrentPlan}
            className={`mt-6 w-full py-3 rounded-lg font-bold transition-all ${
              isCurrentPlan ? 'bg-[var(--border-light)] text-[var(--text-muted)] cursor-not-allowed' :
              isPro ? 'btn-primary' : 'btn-secondary'
            }`}
          >
            {isCurrentPlan ? t.currentPlan : t.selectPlan}
          </button>
        ) : (
          <Link
            to="/login"
            className={`mt-6 block w-full py-3 rounded-lg font-bold text-center transition-all ${
              isPro ? 'btn-primary' : 'btn-secondary'
            }`}
          >
            {t.loginToSubscribe}
          </Link>
        )}
      </div>
    </div>
  );
}

interface FeatureComparisonTableProps {
  t: typeof SUBSCRIPTION_TRANSLATIONS.zh;
}

function FeatureComparisonTable({ t }: FeatureComparisonTableProps) {
  return (
    <div className="mt-16">
      <h3 className="text-xl font-bold text-[var(--text-dark)] mb-6 text-center">{t.featureComparison}</h3>
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-[var(--primary-bg)]">
                <th className="py-4 px-6 text-left text-sm font-bold text-[var(--text-dark)]">{t.featureTableHeaders.feature}</th>
                <th className="py-4 px-6 text-center text-sm font-bold text-[var(--text-muted)]">{t.featureTableHeaders.free}</th>
                <th className="py-4 px-6 text-center text-sm font-bold text-blue-600">{t.featureTableHeaders.basic}</th>
                <th className="py-4 px-6 text-center text-sm font-bold text-[var(--primary)]">{t.featureTableHeaders.pro}</th>
              </tr>
            </thead>
            <tbody>
              {t.features.map((feature, index) => (
                <tr key={index} className="border-b border-[var(--border-light)]">
                  <td className="py-4 px-6 text-sm text-[var(--text-dark)]">{feature.name}</td>
                  <td className="py-4 px-6 text-center text-sm text-[var(--text-muted)]">{feature.free}</td>
                  <td className="py-4 px-6 text-center text-sm text-[var(--text-dark)]">{feature.basic}</td>
                  <td className="py-4 px-6 text-center text-sm font-medium text-[var(--primary)]">{feature.pro}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default SubscriptionPage;
