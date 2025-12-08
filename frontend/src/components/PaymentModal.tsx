/**
 * 支付模态框组件
 * Requirements: 4.2, 4.3, 4.4, 4.9
 * 
 * 功能：
 * - 显示支付方式选择
 * - 显示支付二维码
 * - 轮询支付状态
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiService } from '../services/api';
import type { PlanResponse, PaymentMethod, OrderResponse, PaymentStatus } from '../types';

interface PaymentModalProps {
  isOpen: boolean;
  plan: PlanResponse;
  onClose: () => void;
  onSuccess: () => void;
}

export function PaymentModal({ isOpen, plan, onClose, onSuccess }: PaymentModalProps) {
  // 支付方式
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>('alipay');
  
  // 订单状态
  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [isCreatingOrder, setIsCreatingOrder] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 轮询状态
  const [isPolling, setIsPolling] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | null>(null);
  const pollingIntervalRef = useRef<number | null>(null);
  const pollingTimeoutRef = useRef<number | null>(null);

  // 支付方式配置
  const paymentMethods: { method: PaymentMethod; name: string; icon: string }[] = [
    { method: 'alipay', name: '支付宝', icon: '💳' },
    { method: 'wechat', name: '微信支付', icon: '💬' },
    { method: 'unionpay', name: '银联支付', icon: '🏦' },
  ];

  /**
   * 创建订单
   */
  const createOrder = useCallback(async () => {
    setIsCreatingOrder(true);
    setError(null);
    setOrder(null);
    setPaymentStatus(null);
    
    try {
      const response = await apiService.createOrder({
        plan: plan.plan,
        method: selectedMethod,
      });
      setOrder(response);
      
      // 开始轮询支付状态
      startPolling(response.order_id);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '创建订单失败';
      setError(errorMessage);
    } finally {
      setIsCreatingOrder(false);
    }
  }, [plan.plan, selectedMethod]);

  /**
   * 开始轮询支付状态
   */
  const startPolling = useCallback((orderId: string) => {
    setIsPolling(true);
    
    // 每 3 秒轮询一次
    pollingIntervalRef.current = window.setInterval(async () => {
      try {
        const status = await apiService.getOrderStatus(orderId);
        setPaymentStatus(status.status);
        
        if (status.status === 'paid') {
          stopPolling();
          onSuccess();
        } else if (status.status === 'failed' || status.status === 'expired') {
          stopPolling();
          setError(status.status === 'expired' ? '订单已过期，请重新创建' : '支付失败，请重试');
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000);
    
    // 5 分钟后停止轮询
    pollingTimeoutRef.current = window.setTimeout(() => {
      stopPolling();
      setError('支付超时，请重新创建订单');
    }, 5 * 60 * 1000);
  }, [onSuccess]);

  /**
   * 停止轮询
   */
  const stopPolling = useCallback(() => {
    setIsPolling(false);
    
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    
    if (pollingTimeoutRef.current) {
      clearTimeout(pollingTimeoutRef.current);
      pollingTimeoutRef.current = null;
    }
  }, []);

  /**
   * 关闭模态框时清理
   */
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  /**
   * 重置状态
   */
  const handleReset = () => {
    stopPolling();
    setOrder(null);
    setError(null);
    setPaymentStatus(null);
  };

  /**
   * 关闭模态框
   */
  const handleClose = () => {
    stopPolling();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-gray-800 rounded-xl max-w-md w-full mx-4 border border-gray-700 overflow-hidden">
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h3 className="text-lg font-medium text-white">
            {order ? '完成支付' : '选择支付方式'}
          </h3>
          <button
            onClick={handleClose}
            className="p-1 text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 内容 */}
        <div className="p-6">
          {/* 计划信息 */}
          <div className="mb-6 p-4 bg-gray-700/50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">{plan.name}</span>
              <span className="text-xl font-bold text-white">{plan.price_display}</span>
            </div>
            <p className="mt-1 text-sm text-gray-400">{plan.description}</p>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
              <button
                onClick={handleReset}
                className="ml-2 text-red-300 hover:text-red-200 underline"
              >
                重试
              </button>
            </div>
          )}

          {/* 未创建订单时显示支付方式选择 */}
          {!order && (
            <PaymentMethodSelector
              methods={paymentMethods}
              selectedMethod={selectedMethod}
              onSelect={setSelectedMethod}
              isDisabled={isCreatingOrder}
            />
          )}

          {/* 已创建订单时显示支付信息 */}
          {order && (
            <PaymentInfo
              order={order}
              selectedMethod={selectedMethod}
              isPolling={isPolling}
              paymentStatus={paymentStatus}
            />
          )}
        </div>

        {/* 底部按钮 */}
        <div className="p-4 border-t border-gray-700">
          {!order ? (
            <button
              onClick={createOrder}
              disabled={isCreatingOrder}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isCreatingOrder && (
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white" />
              )}
              {isCreatingOrder ? '创建订单中...' : '确认支付'}
            </button>
          ) : (
            <div className="flex gap-3">
              <button
                onClick={handleReset}
                className="flex-1 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
              >
                更换支付方式
              </button>
              <button
                onClick={handleClose}
                className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
              >
                我已完成支付
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


/**
 * 支付方式选择器组件
 */
interface PaymentMethodSelectorProps {
  methods: { method: PaymentMethod; name: string; icon: string }[];
  selectedMethod: PaymentMethod;
  onSelect: (method: PaymentMethod) => void;
  isDisabled: boolean;
}

function PaymentMethodSelector({ 
  methods, 
  selectedMethod, 
  onSelect, 
  isDisabled 
}: PaymentMethodSelectorProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-400 mb-3">请选择支付方式</p>
      {methods.map(({ method, name, icon }) => (
        <button
          key={method}
          onClick={() => onSelect(method)}
          disabled={isDisabled}
          className={`w-full p-4 rounded-lg border transition-all flex items-center gap-3 ${
            selectedMethod === method
              ? 'border-indigo-500 bg-indigo-500/10'
              : 'border-gray-600 hover:border-gray-500 bg-gray-700/30'
          } ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <span className="text-2xl">{icon}</span>
          <span className="text-white font-medium">{name}</span>
          {selectedMethod === method && (
            <svg className="w-5 h-5 text-indigo-400 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </button>
      ))}
    </div>
  );
}

/**
 * 支付信息组件
 */
interface PaymentInfoProps {
  order: OrderResponse;
  selectedMethod: PaymentMethod;
  isPolling: boolean;
  paymentStatus: PaymentStatus | null;
}

function PaymentInfo({ order, selectedMethod, isPolling, paymentStatus }: PaymentInfoProps) {
  const getMethodName = (method: PaymentMethod) => {
    switch (method) {
      case 'alipay':
        return '支付宝';
      case 'wechat':
        return '微信';
      case 'unionpay':
        return '银联';
    }
  };

  const getStatusText = (status: PaymentStatus | null) => {
    switch (status) {
      case 'pending':
        return '等待支付';
      case 'paid':
        return '支付成功';
      case 'failed':
        return '支付失败';
      case 'expired':
        return '订单过期';
      default:
        return '等待支付';
    }
  };

  const getStatusColor = (status: PaymentStatus | null) => {
    switch (status) {
      case 'paid':
        return 'text-green-400';
      case 'failed':
      case 'expired':
        return 'text-red-400';
      default:
        return 'text-yellow-400';
    }
  };

  return (
    <div className="space-y-4">
      {/* 订单信息 */}
      <div className="text-center">
        <p className="text-sm text-gray-400 mb-2">
          请使用{getMethodName(selectedMethod)}扫描下方二维码完成支付
        </p>
        <p className="text-lg font-bold text-white">{order.amount_display}</p>
      </div>

      {/* 二维码区域 */}
      <div className="flex justify-center">
        {order.qrcode_content ? (
          <QRCodeDisplay content={order.qrcode_content} />
        ) : order.payment_url ? (
          <div className="text-center">
            <p className="text-sm text-gray-400 mb-3">点击下方按钮跳转支付</p>
            <a
              href={order.payment_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
            >
              前往{getMethodName(selectedMethod)}支付
            </a>
          </div>
        ) : (
          <div className="w-48 h-48 bg-gray-700 rounded-lg flex items-center justify-center">
            <span className="text-gray-500">二维码加载中...</span>
          </div>
        )}
      </div>

      {/* 支付状态 */}
      <div className="flex items-center justify-center gap-2">
        {isPolling && paymentStatus !== 'paid' && (
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-indigo-500/30 border-t-indigo-500" />
        )}
        <span className={`text-sm ${getStatusColor(paymentStatus)}`}>
          {getStatusText(paymentStatus)}
        </span>
      </div>

      {/* 订单号 */}
      <p className="text-center text-xs text-gray-500">
        订单号：{order.order_id}
      </p>

      {/* 倒计时提示 */}
      {order.expires_in_seconds > 0 && (
        <CountdownTimer initialSeconds={order.expires_in_seconds} />
      )}
    </div>
  );
}

/**
 * 二维码显示组件
 * 使用简单的 SVG 占位符，实际项目中应使用 qrcode 库
 */
interface QRCodeDisplayProps {
  content: string;
}

function QRCodeDisplay({ content: _content }: QRCodeDisplayProps) {
  // 实际项目中应使用 qrcode.react 或类似库生成真实二维码
  // 这里使用占位符展示，content 参数用于生成二维码
  return (
    <div className="w-48 h-48 bg-white rounded-lg p-2 flex items-center justify-center">
      <div className="w-full h-full bg-gray-100 rounded flex flex-col items-center justify-center">
        <svg className="w-16 h-16 text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
        </svg>
        <span className="text-xs text-gray-500 text-center px-2">
          扫码支付
        </span>
      </div>
    </div>
  );
}

/**
 * 倒计时组件
 */
interface CountdownTimerProps {
  initialSeconds: number;
}

function CountdownTimer({ initialSeconds }: CountdownTimerProps) {
  const [seconds, setSeconds] = useState(initialSeconds);

  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (seconds <= 0) {
    return (
      <p className="text-center text-sm text-red-400">
        订单已过期，请重新创建
      </p>
    );
  }

  return (
    <p className="text-center text-sm text-gray-400">
      请在 <span className="text-yellow-400 font-medium">
        {minutes}:{remainingSeconds.toString().padStart(2, '0')}
      </span> 内完成支付
    </p>
  );
}

export default PaymentModal;
