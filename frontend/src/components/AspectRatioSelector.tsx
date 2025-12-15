/**
 * 尺寸选择器组件
 * Requirements: 5.1, 5.2, 5.3 - 支持多种输出尺寸
 */

import type { AspectRatio, Language } from '../types';
import { TRANSLATIONS } from '../constants/locales';

interface AspectRatioSelectorProps {
  value: AspectRatio;
  onChange: (value: AspectRatio) => void;
  customWidth?: number;
  customHeight?: number;
  onCustomChange?: (width: number, height: number) => void;
  language?: Language;
  disabled?: boolean;
}

interface RatioOption {
  value: AspectRatio;
  label: string;
  description: string;
  icon: string;
  dimensions: string;
}

export function AspectRatioSelector({
  value,
  onChange,
  customWidth = 1024,
  customHeight = 1024,
  onCustomChange,
  language = 'zh',
  disabled = false,
}: AspectRatioSelectorProps) {
  const t = TRANSLATIONS[language];
  
  const ratioOptions: RatioOption[] = [
    {
      value: '1:1',
      label: t.aspectRatios.square,
      description: t.aspectRatios.social,
      icon: '⬜',
      dimensions: '1024×1024',
    },
    {
      value: '9:16',
      label: t.aspectRatios.portrait,
      description: t.aspectRatios.story,
      icon: '📱',
      dimensions: '576×1024',
    },
    {
      value: '16:9',
      label: t.aspectRatios.landscape,
      description: t.aspectRatios.video,
      icon: '🖥️',
      dimensions: '1024×576',
    },
    {
      value: 'custom',
      label: t.aspectRatios.custom,
      description: t.aspectRatios.customDesc,
      icon: '🔧',
      dimensions: '???×???',
    },
  ];

  const handleWidthChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value);
    if (!isNaN(val) && onCustomChange) {
      onCustomChange(val, customHeight);
    }
  };

  const handleHeightChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value);
    if (!isNaN(val) && onCustomChange) {
      onCustomChange(customWidth, val);
    }
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-[var(--text-dark)]">{t.form.sizeLabel}</label>
      <div className="grid grid-cols-4 gap-2">
        {ratioOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            disabled={disabled}
            className={`relative p-3 rounded-lg border transition-all duration-200 group ${
              value === option.value
                ? 'border-[var(--primary)] bg-[var(--primary-bg)] ring-1 ring-[var(--primary)]'
                : 'border-[var(--border-light)] bg-white hover:border-[var(--primary)] hover:bg-[var(--primary-bg)]'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            aria-pressed={value === option.value}
            title={`${option.label} - ${option.description}`}
          >
            {/* Aspect Ratio Visual */}
            <div className="flex justify-center mb-2">
              <div
                className={`rounded flex items-center justify-center transition-colors ${
                  option.value === '1:1'
                    ? 'w-6 h-6'
                    : option.value === '9:16'
                    ? 'w-5 h-8'
                    : option.value === '16:9'
                    ? 'w-8 h-5'
                    : 'w-6 h-6'
                } ${
                  value === option.value ? 'bg-[var(--primary)] text-white' : 'bg-[var(--border-light)] text-[var(--text-muted)]'
                }`}
              >
                <span className="text-xs">{option.icon}</span>
              </div>
            </div>

            {/* Label */}
            <p className={`text-xs font-medium text-center transition-colors truncate ${
                value === option.value ? 'text-[var(--primary)]' : 'text-[var(--text-dark)]'
            }`}>
              {option.label}
            </p>

            {/* Selected Indicator */}
            {value === option.value && (
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-[var(--primary)] rounded-full flex items-center justify-center shadow-sm">
                <svg
                  className="w-2.5 h-2.5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Dimensions Display */}
      {value !== 'custom' && (
        <p className="text-xs text-[var(--text-muted)] text-center">
          {ratioOptions.find(o => o.value === value)?.dimensions} · {ratioOptions.find(o => o.value === value)?.description}
        </p>
      )}

      {/* Custom Dimensions Inputs */}
      {value === 'custom' && (
        <div className="grid grid-cols-2 gap-3 p-3 bg-[var(--primary-bg)] border border-[var(--border-light)] rounded-lg">
          <div className="space-y-1">
            <label className="block text-xs text-[var(--text-muted)]">{t.form.width}</label>
            <div className="relative">
              <input
                type="number"
                value={customWidth}
                onChange={handleWidthChange}
                min={256}
                max={2048}
                step={8}
                disabled={disabled}
                className="w-full px-3 py-2 bg-white border border-[var(--border-light)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-[var(--primary)] transition-all"
              />
              <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)]">px</span>
            </div>
          </div>
          <div className="space-y-1">
            <label className="block text-xs text-[var(--text-muted)]">{t.form.height}</label>
            <div className="relative">
              <input
                type="number"
                value={customHeight}
                onChange={handleHeightChange}
                min={256}
                max={2048}
                step={8}
                disabled={disabled}
                className="w-full px-3 py-2 bg-white border border-[var(--border-light)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-[var(--primary)] transition-all"
              />
              <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)]">px</span>
            </div>
          </div>
          <p className="col-span-2 text-xs text-[var(--text-muted)] text-center">
            {language === 'zh' ? '范围: 256-2048 像素，8的倍数' : 'Range: 256-2048 px, multiples of 8'}
          </p>
        </div>
      )}
    </div>
  );
}

export default AspectRatioSelector;
