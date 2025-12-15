/**
 * 场景描述输入框组件
 * Requirements: 1.1 - 支持输入画面描述
 */

import type { ChangeEvent } from 'react';
import type { Language } from '../types';
import { TRANSLATIONS } from '../constants/locales';

interface SceneDescriptionInputProps {
  value: string;
  onChange: (value: string) => void;
  language: Language;
  disabled?: boolean;
}

export function SceneDescriptionInput({
  value,
  onChange,
  language,
  disabled = false,
}: SceneDescriptionInputProps) {
  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  const t = TRANSLATIONS[language].form;

  return (
    <div className="space-y-2">
      <label
        htmlFor="scene-description"
        className="block text-sm font-medium text-[var(--text-dark)]"
      >
        {t.sceneLabel}
      </label>
      <div className="relative group">
        <textarea
          id="scene-description"
          value={value}
          onChange={handleChange}
          disabled={disabled}
          placeholder={t.scenePlaceholder}
          className="w-full min-h-[140px] px-4 py-3 bg-white border border-[var(--border-light)] rounded-lg text-[var(--text-dark)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-[var(--primary)] resize-y disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          aria-describedby="scene-description-hint"
        />
        <div className="absolute bottom-3 right-3 pointer-events-none">
           <svg className="w-4 h-4 text-[var(--text-muted)] group-focus-within:text-[var(--primary)] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
           </svg>
        </div>
      </div>
      <p id="scene-description-hint" className="text-xs text-[var(--text-muted)]">
        {t.sceneHint}
      </p>
    </div>
  );
}

export default SceneDescriptionInput;
