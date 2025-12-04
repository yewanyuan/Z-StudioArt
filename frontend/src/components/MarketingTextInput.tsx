/**
 * 文案输入框组件
 * Requirements: 1.1, 1.2 - 支持中英文文案输入
 */

import type { ChangeEvent } from 'react';
import type { Language } from '../types';
import { TRANSLATIONS } from '../constants/locales';

interface MarketingTextInputProps {
  value: string;
  onChange: (value: string) => void;
  language: Language;
  onLanguageChange: (language: Language) => void;
  disabled?: boolean;
}

export function MarketingTextInput({
  value,
  onChange,
  language,
  onLanguageChange,
  disabled = false,
}: MarketingTextInputProps) {
  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  const t = TRANSLATIONS[language].form;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label
          htmlFor="marketing-text"
          className="block text-xs font-semibold text-gray-300 uppercase tracking-wider ml-1"
        >
          {t.marketingLabel}
        </label>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg overflow-hidden border border-white/10 bg-black/20 p-0.5">
            <button
              type="button"
              onClick={() => onLanguageChange('zh')}
              disabled={disabled}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                language === 'zh'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
              } disabled:opacity-50`}
              aria-pressed={language === 'zh'}
            >
              中文
            </button>
            <button
              type="button"
              onClick={() => onLanguageChange('en')}
              disabled={disabled}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                language === 'en'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
              } disabled:opacity-50`}
              aria-pressed={language === 'en'}
            >
              English
            </button>
          </div>
        </div>
      </div>
      <div className="relative group">
        <textarea
          id="marketing-text"
          value={value}
          onChange={handleTextChange}
          disabled={disabled}
          placeholder={t.marketingPlaceholder}
          className="w-full h-24 px-4 py-3 bg-black/20 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 resize-none disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:bg-black/30"
          aria-describedby="marketing-text-hint"
        />
        <div className="absolute bottom-3 right-3 pointer-events-none">
          <svg className="w-4 h-4 text-gray-600 group-focus-within:text-indigo-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </div>
      </div>
      <p id="marketing-text-hint" className="text-xs text-gray-500 ml-1">
        {t.marketingHint}
      </p>
    </div>
  );
}

export default MarketingTextInput;
