/**
 * 注册页面组件
 * Based on Mathilda Art Gallery Template - Contact Form Style
 * 支持手机验证码注册和邮箱密码注册
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { apiService } from '../services/api';

type RegisterMethod = 'phone' | 'email';

export function RegisterPage() {
  const navigate = useNavigate();
  const { setAuth, isAuthenticated } = useAuthStore();

  // 注册方式
  const [registerMethod, setRegisterMethod] = useState<RegisterMethod>('phone');

  // 手机注册表单
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [isSendingCode, setIsSendingCode] = useState(false);

  // 邮箱注册表单
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // 状态
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // 已登录则跳转
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // 验证码倒计时
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  // 验证手机号格式
  const isValidPhone = (value: string) => /^1[3-9]\d{9}$/.test(value);

  // 验证邮箱格式
  const isValidEmail = (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);

  // 验证密码匹配
  useEffect(() => {
    if (confirmPassword && password !== confirmPassword) {
      setPasswordError('两次输入的密码不一致');
    } else {
      setPasswordError(null);
    }
  }, [password, confirmPassword]);

  // 发送验证码
  const handleSendCode = useCallback(async () => {
    if (!isValidPhone(phone) || countdown > 0 || isSendingCode) return;

    setIsSendingCode(true);
    setError(null);

    try {
      await apiService.sendVerificationCode(phone);
      setCountdown(60);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '发送验证码失败，请稍后重试';
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || errorMessage);
      } else {
        setError(errorMessage);
      }
    } finally {
      setIsSendingCode(false);
    }
  }, [phone, countdown, isSendingCode]);

  // 手机号注册
  const handlePhoneRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValidPhone(phone) || code.length !== 6 || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await apiService.registerWithPhone(phone, code);
      // 注册成功自动登录
      setAuth(response.user, response.tokens.access_token, response.tokens.refresh_token);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '注册失败，请稍后重试';
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || errorMessage);
      } else {
        setError(errorMessage);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // 邮箱注册
  const handleEmailRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValidEmail(email) || password.length < 8 || password !== confirmPassword || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await apiService.registerWithEmail(email, password);
      // 注册成功自动登录
      setAuth(response.user, response.tokens.access_token, response.tokens.refresh_token);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '注册失败，请稍后重试';
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || errorMessage);
      } else {
        setError(errorMessage);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // 表单是否可提交
  const canSubmitPhone = isValidPhone(phone) && code.length === 6 && !isSubmitting;
  const canSubmitEmail = isValidEmail(email) && password.length >= 8 && password === confirmPassword && !isSubmitting;

  return (
    <div className="min-h-screen bg-white relative">
      {/* Background Curve */}
      <div className="bg-curve" />

      {/* Content */}
      <div className="min-h-screen flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md animate-fadeIn">
          {/* Logo */}
          <div className="text-center mb-8">
            <Link to="/" className="inline-block mb-6">
              <img src="/img/logo.png" alt="PopGraph Studio" className="h-16 mx-auto" />
            </Link>
            <h2 className="text-[var(--primary)] mb-2">创建账户</h2>
            <p className="text-[var(--text-muted)]">注册 PopGraph 开始创作</p>
          </div>

          {/* Register Card */}
          <div className="card">
            <div className="card-body p-8">
              {/* Tab Switcher */}
              <div className="flex mb-6 p-1 bg-[var(--primary-bg)] rounded-lg">
                <button
                  type="button"
                  onClick={() => {
                    setRegisterMethod('phone');
                    setError(null);
                  }}
                  className={`flex-1 py-3 text-sm font-bold rounded-md transition-all ${
                    registerMethod === 'phone'
                      ? 'bg-[var(--primary)] text-white shadow-lg'
                      : 'text-[var(--text-muted)] hover:text-[var(--primary)]'
                  }`}
                >
                  手机注册
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setRegisterMethod('email');
                    setError(null);
                  }}
                  className={`flex-1 py-3 text-sm font-bold rounded-md transition-all ${
                    registerMethod === 'email'
                      ? 'bg-[var(--primary)] text-white shadow-lg'
                      : 'text-[var(--text-muted)] hover:text-[var(--primary)]'
                  }`}
                >
                  邮箱注册
                </button>
              </div>

              {/* Error Message */}
              {error && (
                <div className="alert alert-error flex items-start gap-3">
                  <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="text-sm">{error}</p>
                </div>
              )}

              {/* Phone Register Form */}
              {registerMethod === 'phone' && (
                <form onSubmit={handlePhoneRegister} className="space-y-5">
                  {/* Phone Input */}
                  <div>
                    <label htmlFor="phone" className="form-label">
                      手机号
                    </label>
                    <input
                      id="phone"
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 11))}
                      placeholder="请输入手机号"
                      disabled={isSubmitting}
                      className="form-input"
                    />
                  </div>

                  {/* Verification Code Input */}
                  <div>
                    <label htmlFor="code" className="form-label">
                      验证码
                    </label>
                    {/* Stack vertically on mobile, horizontal on desktop */}
                    <div className="flex flex-col sm:flex-row gap-3">
                      <input
                        id="code"
                        type="text"
                        value={code}
                        onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        placeholder="请输入验证码"
                        disabled={isSubmitting}
                        className="form-input sm:flex-1"
                      />
                      <button
                        type="button"
                        onClick={handleSendCode}
                        disabled={!isValidPhone(phone) || countdown > 0 || isSendingCode}
                        className="btn-secondary whitespace-nowrap sm:min-w-[120px] disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isSendingCode ? (
                          <span className="flex items-center justify-center gap-2">
                            <div className="w-4 h-4 border-2 border-[var(--primary)] border-t-transparent rounded-full animate-spin" />
                          </span>
                        ) : countdown > 0 ? (
                          `${countdown}s`
                        ) : (
                          '获取验证码'
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={!canSubmitPhone}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>注册中...</span>
                      </>
                    ) : (
                      '注册'
                    )}
                  </button>
                </form>
              )}

              {/* Email Register Form */}
              {registerMethod === 'email' && (
                <form onSubmit={handleEmailRegister} className="space-y-5">
                  {/* Email Input */}
                  <div>
                    <label htmlFor="email" className="form-label">
                      邮箱
                    </label>
                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="请输入邮箱"
                      disabled={isSubmitting}
                      className="form-input"
                    />
                  </div>

                  {/* Password Input */}
                  <div>
                    <label htmlFor="password" className="form-label">
                      密码
                    </label>
                    <input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="请输入密码（至少8位）"
                      disabled={isSubmitting}
                      className="form-input"
                    />
                  </div>

                  {/* Confirm Password Input */}
                  <div>
                    <label htmlFor="confirmPassword" className="form-label">
                      确认密码
                    </label>
                    <input
                      id="confirmPassword"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="请再次输入密码"
                      disabled={isSubmitting}
                      className={`form-input ${passwordError ? 'border-red-500' : ''}`}
                    />
                    {passwordError && (
                      <p className="mt-2 text-sm text-red-500">{passwordError}</p>
                    )}
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={!canSubmitEmail}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>注册中...</span>
                      </>
                    ) : (
                      '注册'
                    )}
                  </button>
                </form>
              )}

              {/* Login Link */}
              <div className="mt-6 text-center">
                <p className="text-[var(--text-muted)] text-sm">
                  已有账户？{' '}
                  <Link to="/login" className="text-[var(--primary)] hover:text-[var(--primary-dark)] font-semibold transition-colors">
                    立即登录
                  </Link>
                </p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <p className="text-center text-[var(--text-muted)] text-xs mt-6">
            注册即表示您同意我们的服务条款和隐私政策
          </p>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;
