/**
 * 模板选择器组件
 * Requirements: 3.1, 3.2, 3.3 - 预设商业模板选择
 */

import { useState, useEffect } from 'react';
import type { Template, TemplateCategory, Language } from '../types';
import { apiService } from '../services/api';
import { TRANSLATIONS } from '../constants/locales';

interface TemplateSelectorProps {
  selectedTemplateId?: string;
  onSelect: (templateId: string | undefined) => void;
  language: Language;
  disabled?: boolean;
}

const CATEGORY_COLORS: Record<TemplateCategory, string> = {
  promotional: 'bg-red-600',
  premium: 'bg-amber-600',
  holiday: 'bg-pink-600',
};

export function TemplateSelector({
  selectedTemplateId,
  onSelect,
  language,
  disabled = false,
}: TemplateSelectorProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [activeCategory, setActiveCategory] = useState<TemplateCategory | 'all'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>();

  const t = TRANSLATIONS[language];

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setIsLoading(true);
      setError(undefined);
      const data = await apiService.getTemplates();
      setTemplates(data);
    } catch (err) {
      setError('加载模板失败，请稍后重试'); // This error message comes from API, maybe we can translate it too but usually API errors are dynamic. For now leaving as is or generic.
      console.error('Failed to load templates:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredTemplates =
    activeCategory === 'all'
      ? templates
      : templates.filter((t) => t.category === activeCategory);

  const categories: (TemplateCategory | 'all')[] = ['all', 'promotional', 'premium', 'holiday'];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider ml-1">
          {t.form.templateLabel} <span className="text-gray-500 font-normal normal-case">{t.form.templateOptional}</span>
        </label>
        {selectedTemplateId && (
          <button
            type="button"
            onClick={() => onSelect(undefined)}
            disabled={disabled}
            className="text-xs text-indigo-300 hover:text-indigo-200 disabled:opacity-50 transition-colors"
          >
            {t.form.clearTemplate}
          </button>
        )}
      </div>

      {/* Category Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {categories.map((category) => (
          <button
            key={category}
            type="button"
            onClick={() => setActiveCategory(category)}
            disabled={disabled}
            className={`px-4 py-1.5 text-xs font-medium rounded-full whitespace-nowrap transition-all duration-200 border ${
              activeCategory === category
                ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/30'
                : 'bg-black/20 border-white/10 text-gray-400 hover:bg-white/5 hover:text-gray-200'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {t.categories[category]}
          </button>
        ))}
      </div>

      {/* Template Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center h-40 text-gray-400">
          <p className="text-sm">{error}</p>
          <button
            type="button"
            onClick={loadTemplates}
            className="mt-2 text-xs text-indigo-400 hover:text-indigo-300"
          >
            {t.form.retry}
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {filteredTemplates.map((template) => (
            <button
              key={template.id}
              type="button"
              onClick={() => onSelect(template.id)}
              disabled={disabled}
              className={`relative group p-3 rounded-xl border transition-all duration-300 text-left ${
                selectedTemplateId === template.id
                  ? 'border-indigo-500 bg-indigo-500/10 ring-1 ring-indigo-500/50 shadow-[0_0_15px_rgba(99,102,241,0.3)]'
                  : 'border-white/10 bg-black/20 hover:bg-white/5 hover:border-white/20 hover:-translate-y-1'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {/* Category Badge */}
              <span
                className={`absolute top-2 right-2 px-1.5 py-0.5 text-[10px] font-bold tracking-wider uppercase text-white rounded shadow-sm z-10 ${
                  CATEGORY_COLORS[template.category]
                }`}
              >
                {t.categories[template.category]}
              </span>

              {/* Template Preview Placeholder */}
              <div className="w-full h-20 rounded-lg mb-3 overflow-hidden relative">
                <div className="absolute inset-0 bg-gradient-to-br from-slate-700 to-slate-800 group-hover:scale-105 transition-transform duration-500" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl filter drop-shadow-lg transform group-hover:scale-110 transition-transform duration-300">
                    {template.category === 'promotional' && '🏷️'}
                    {template.category === 'premium' && '✨'}
                    {template.category === 'holiday' && '🎉'}
                  </span>
                </div>
              </div>

              {/* Template Name */}
              <p className="text-sm font-semibold text-gray-200 truncate group-hover:text-white transition-colors">{template.name}</p>
              <p className="text-xs text-gray-500 truncate mt-0.5">
                {template.prompt_modifiers.color_scheme}
              </p>

              {/* Selected Indicator */}
              {selectedTemplateId === template.id && (
                <div className="absolute -top-1 -left-1 w-5 h-5 bg-indigo-500 rounded-full flex items-center justify-center shadow-lg border border-white/20">
                  <svg
                    className="w-3 h-3 text-white"
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
      )}
    </div>
  );
}

export default TemplateSelector;
