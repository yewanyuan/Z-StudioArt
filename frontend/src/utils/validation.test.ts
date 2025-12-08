/**
 * 验证工具函数测试
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import {
  isValidPhone,
  isValidEmail,
  isValidPassword,
  isValidVerificationCode,
  formatPhoneDisplay,
  formatPrice,
  formatDate,
  getDaysRemaining,
} from './validation';

describe('isValidPhone', () => {
  it('应该接受有效的中国手机号', () => {
    expect(isValidPhone('13800138000')).toBe(true);
    expect(isValidPhone('15912345678')).toBe(true);
    expect(isValidPhone('18888888888')).toBe(true);
    expect(isValidPhone('19900001111')).toBe(true);
  });

  it('应该拒绝无效的手机号', () => {
    expect(isValidPhone('')).toBe(false);
    expect(isValidPhone('1234567890')).toBe(false);
    expect(isValidPhone('12345678901')).toBe(false); // 以 1 开头但第二位是 2
    expect(isValidPhone('138001380001')).toBe(false); // 12 位
    expect(isValidPhone('1380013800')).toBe(false); // 10 位
    expect(isValidPhone('abc')).toBe(false);
  });

  // 属性测试：有效手机号长度为 11 位
  it('属性测试：有效手机号长度为 11 位', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 130, max: 199 }),
        fc.integer({ min: 0, max: 99999999 }),
        (prefix, suffix) => {
          const phone = `${prefix}${suffix.toString().padStart(8, '0')}`;
          if (isValidPhone(phone)) {
            expect(phone.length).toBe(11);
          }
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});

describe('isValidEmail', () => {
  it('应该接受有效的邮箱', () => {
    expect(isValidEmail('test@example.com')).toBe(true);
    expect(isValidEmail('user.name@domain.co')).toBe(true);
    expect(isValidEmail('a@b.c')).toBe(true);
  });

  it('应该拒绝无效的邮箱', () => {
    expect(isValidEmail('')).toBe(false);
    expect(isValidEmail('test')).toBe(false);
    expect(isValidEmail('test@')).toBe(false);
    expect(isValidEmail('@example.com')).toBe(false);
    expect(isValidEmail('test@example')).toBe(false);
  });
});

describe('isValidPassword', () => {
  it('应该接受 8 位及以上的密码', () => {
    expect(isValidPassword('12345678')).toBe(true);
    expect(isValidPassword('password123')).toBe(true);
    expect(isValidPassword('a'.repeat(100))).toBe(true);
  });

  it('应该拒绝少于 8 位的密码', () => {
    expect(isValidPassword('')).toBe(false);
    expect(isValidPassword('1234567')).toBe(false);
    expect(isValidPassword('abc')).toBe(false);
  });

  // 属性测试：长度 >= 8 的字符串应该有效
  it('属性测试：长度 >= 8 的字符串应该有效', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 8, maxLength: 100 }),
        (password) => {
          return isValidPassword(password) === true;
        }
      ),
      { numRuns: 100 }
    );
  });

  // 属性测试：长度 < 8 的字符串应该无效
  it('属性测试：长度 < 8 的字符串应该无效', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 0, maxLength: 7 }),
        (password) => {
          return isValidPassword(password) === false;
        }
      ),
      { numRuns: 100 }
    );
  });
});

describe('isValidVerificationCode', () => {
  it('应该接受 6 位数字验证码', () => {
    expect(isValidVerificationCode('123456')).toBe(true);
    expect(isValidVerificationCode('000000')).toBe(true);
    expect(isValidVerificationCode('999999')).toBe(true);
  });

  it('应该拒绝无效的验证码', () => {
    expect(isValidVerificationCode('')).toBe(false);
    expect(isValidVerificationCode('12345')).toBe(false);
    expect(isValidVerificationCode('1234567')).toBe(false);
    expect(isValidVerificationCode('abcdef')).toBe(false);
    expect(isValidVerificationCode('12345a')).toBe(false);
  });

  // 属性测试：6 位数字应该有效
  it('属性测试：6 位数字应该有效', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 999999 }),
        (num) => {
          const code = num.toString().padStart(6, '0');
          return isValidVerificationCode(code) === true;
        }
      ),
      { numRuns: 100 }
    );
  });
});

describe('formatPhoneDisplay', () => {
  it('应该正确隐藏手机号中间 4 位', () => {
    expect(formatPhoneDisplay('13800138000')).toBe('138****8000');
    expect(formatPhoneDisplay('15912345678')).toBe('159****5678');
  });

  it('无效手机号应该原样返回', () => {
    expect(formatPhoneDisplay('123')).toBe('123');
    expect(formatPhoneDisplay('')).toBe('');
  });
});

describe('formatPrice', () => {
  it('应该正确将分转换为元', () => {
    expect(formatPrice(100)).toBe('¥1.00');
    expect(formatPrice(2999)).toBe('¥29.99');
    expect(formatPrice(0)).toBe('¥0.00');
    expect(formatPrice(99900)).toBe('¥999.00');
  });

  // 属性测试：格式化后应该以 ¥ 开头
  it('属性测试：格式化后应该以 ¥ 开头', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 10000000 }),
        (cents) => {
          const formatted = formatPrice(cents);
          return formatted.startsWith('¥');
        }
      ),
      { numRuns: 100 }
    );
  });
});

describe('formatDate', () => {
  it('应该正确格式化日期', () => {
    const result = formatDate('2024-12-08T10:30:00Z');
    expect(result).toMatch(/2024/);
    expect(result).toMatch(/12/);
    expect(result).toMatch(/08/);
  });
});

describe('getDaysRemaining', () => {
  it('未来日期应该返回正数', () => {
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 10);
    const days = getDaysRemaining(futureDate.toISOString());
    expect(days).toBeGreaterThan(0);
    expect(days).toBeLessThanOrEqual(11);
  });

  it('过去日期应该返回负数', () => {
    const pastDate = new Date();
    pastDate.setDate(pastDate.getDate() - 10);
    const days = getDaysRemaining(pastDate.toISOString());
    expect(days).toBeLessThan(0);
  });
});
