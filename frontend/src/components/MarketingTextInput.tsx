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
  disabled?: boolean;
}

export function MarketingTextInput({
  value,
  onChange,
  language,
  disabled = false,
}: MarketingTextInputProps) {
  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  const t = TRANSLATIONS[language].form;

  return (
    <div className="space-y-2">
      <label
        htmlFor="marketing-text"
        className="form-label"
      >
        {t.marketingLabel}
      </label>
      <div className="relative">
        <textarea
          id="marketing-text"
          value={value}
          onChange={handleTextChange}
          disabled={disabled}
          placeholder={t.marketingPlaceholder}
          className="form-input min-h-[100px] resize-none"
          aria-describedby="marketing-text-hint"
        />
      </div>
      <p id="marketing-text-hint" className="text-xs text-[var(--text-muted)]">
        {t.marketingHint}
      </p>
    </div>
  );
}

export default MarketingTextInput;
