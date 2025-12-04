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
      <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider ml-1">{t.form.sizeLabel}</label>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {ratioOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            disabled={disabled}
            className={`relative p-4 rounded-xl border transition-all duration-200 group ${
              value === option.value
                ? 'border-indigo-500 bg-indigo-500/10 ring-1 ring-indigo-500/50'
                : 'border-white/10 bg-black/20 hover:bg-white/5 hover:border-white/20 hover:-translate-y-1'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            aria-pressed={value === option.value}
          >
            {/* Aspect Ratio Visual */}
            <div className="flex justify-center mb-3">
              <div
                className={`rounded flex items-center justify-center transition-colors ${
                  option.value === '1:1'
                    ? 'w-8 h-8'
                    : option.value === '9:16'
                    ? 'w-6 h-10'
                    : option.value === '16:9'
                    ? 'w-10 h-6'
                    : 'w-8 h-8'
                } ${
                  value === option.value ? 'bg-indigo-500 text-white' : 'bg-white/10 text-gray-400 group-hover:bg-white/20 group-hover:text-gray-200'
                }`}
              >
                <span className="text-sm">{option.icon}</span>
              </div>
            </div>

            {/* Label */}
            <p className={`text-xs font-semibold text-center transition-colors ${
                value === option.value ? 'text-white' : 'text-gray-300 group-hover:text-white'
            }`}>
              {option.label}
            </p>
            <p className="text-[10px] text-gray-500 text-center mt-0.5">
                {option.description}
            </p>
            {option.value !== 'custom' && (
              <p className="text-[9px] text-gray-600 text-center mt-1 font-mono opacity-60">{option.dimensions}</p>
            )}

            {/* Selected Indicator */}
            {value === option.value && (
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-indigo-500 rounded-full flex items-center justify-center shadow-sm border border-white/20">
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

      {/* Custom Dimensions Inputs */}
      {value === 'custom' && (
        <div className="grid grid-cols-2 gap-4 p-4 bg-white/5 border border-white/10 rounded-xl animate-in fade-in slide-in-from-top-2">
          <div className="space-y-1">
            <label className="block text-[10px] font-medium text-gray-400 uppercase">{t.form.width} ({t.form.pixels})</label>
            <input
              type="number"
              value={customWidth}
              onChange={handleWidthChange}
              min={256}
              max={2048}
              step={8}
              disabled={disabled}
              className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
            />
          </div>
          <div className="space-y-1">
            <label className="block text-[10px] font-medium text-gray-400 uppercase">{t.form.height} ({t.form.pixels})</label>
            <input
              type="number"
              value={customHeight}
              onChange={handleHeightChange}
              min={256}
              max={2048}
              step={8}
              disabled={disabled}
              className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
            />
          </div>
          <p className="col-span-2 text-[10px] text-gray-500 text-center">
            Range: 256 - 2048 px. Sizes must be multiples of 8.
          </p>
        </div>
      )}
    </div>
  );
}

export default AspectRatioSelector;
