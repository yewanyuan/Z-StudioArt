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
        className="block text-xs font-semibold text-gray-300 uppercase tracking-wider ml-1"
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
          className="w-full h-32 px-4 py-3 bg-black/20 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 resize-none disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 ease-in-out hover:bg-black/30"
          aria-describedby="scene-description-hint"
        />
        <div className="absolute bottom-3 right-3 pointer-events-none">
           <svg className="w-4 h-4 text-gray-600 group-focus-within:text-indigo-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
           </svg>
        </div>
      </div>
      <p id="scene-description-hint" className="text-xs text-gray-500 ml-1">
        {t.sceneHint}
      </p>
    </div>
  );
}

export default SceneDescriptionInput;
