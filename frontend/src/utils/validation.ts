/**
 * 表单验证工具函数
 */

/**
 * 验证中国大陆手机号格式
 * @param phone 手机号
 * @returns 是否有效
 */
export function isValidPhone(phone: string): boolean {
  const phoneRegex = /^1[3-9]\d{9}$/;
  return phoneRegex.test(phone);
}

/**
 * 验证邮箱格式
 * @param email 邮箱地址
 * @returns 是否有效
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * 验证密码强度
 * @param password 密码
 * @returns 是否满足最低要求（至少8位）
 */
export function isValidPassword(password: string): boolean {
  return password.length >= 8;
}

/**
 * 验证验证码格式
 * @param code 验证码
 * @returns 是否有效（6位数字）
 */
export function isValidVerificationCode(code: string): boolean {
  const codeRegex = /^\d{6}$/;
  return codeRegex.test(code);
}

/**
 * 格式化手机号显示（隐藏中间4位）
 * @param phone 手机号
 * @returns 格式化后的手机号
 */
export function formatPhoneDisplay(phone: string): string {
  if (!isValidPhone(phone)) return phone;
  return `${phone.slice(0, 3)}****${phone.slice(7)}`;
}

/**
 * 格式化金额显示（分转元）
 * @param cents 金额（分）
 * @returns 格式化后的金额字符串
 */
export function formatPrice(cents: number): string {
  const yuan = cents / 100;
  return `¥${yuan.toFixed(2)}`;
}

/**
 * 格式化日期显示
 * @param dateString ISO 日期字符串
 * @returns 格式化后的日期
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

/**
 * 格式化日期时间显示
 * @param dateString ISO 日期字符串
 * @returns 格式化后的日期时间
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 计算剩余天数
 * @param expiryDateString 过期日期字符串
 * @returns 剩余天数，负数表示已过期
 */
export function getDaysRemaining(expiryDateString: string): number {
  const expiry = new Date(expiryDateString);
  const now = new Date();
  const diffMs = expiry.getTime() - now.getTime();
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
}
