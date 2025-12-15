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
  promotional: 'bg-red-500',
  premium: 'bg-amber-500',
  holiday: 'bg-pink-500',
};

const CATEGORY_ICONS: Record<TemplateCategory, string> = {
  promotional: '🏷️',
  premium: '✨',
  holiday: '🎉',
};

// Template translations - maps template IDs to translated names and descriptions
const TEMPLATE_TRANSLATIONS: Record<string, { zh: { name: string; description: string }; en: { name: string; description: string } }> = {
  // Promotional templates
  'promo-sale-01': {
    zh: { name: '限时特惠', description: '红色醒目配色，适合促销活动' },
    en: { name: 'Flash Sale', description: 'Eye-catching red colors, perfect for promotions' },
  },
  'promo-flash-02': {
    zh: { name: '闪购秒杀', description: '红橙渐变配色，营造紧迫感' },
    en: { name: 'Flash Deal', description: 'Red-orange gradient, creates urgency' },
  },
  'promo-discount-03': {
    zh: { name: '满减优惠', description: '红金配色，突出优惠信息' },
    en: { name: 'Discount Deal', description: 'Red and gold colors, highlights discounts' },
  },
  // Premium templates
  'premium-minimal-01': {
    zh: { name: '极简奢华', description: '黑金配色，大量留白' },
    en: { name: 'Minimal Luxury', description: 'Black and gold with white space' },
  },
  'premium-studio-02': {
    zh: { name: '影棚质感', description: '专业灯光效果，高端质感' },
    en: { name: 'Studio Quality', description: 'Professional lighting, premium feel' },
  },
  'premium-blackgold-03': {
    zh: { name: '黑金尊享', description: '哑光黑金配色，VIP专属感' },
    en: { name: 'Black Gold VIP', description: 'Matte black with gold accents' },
  },
  // Holiday templates
  'holiday-spring-01': {
    zh: { name: '春节喜庆', description: '红金喜庆配色，传统节日风格' },
    en: { name: 'Spring Festival', description: 'Red and gold festive colors' },
  },
  'holiday-valentines-02': {
    zh: { name: '情人节浪漫', description: '粉红浪漫配色，爱情主题' },
    en: { name: 'Valentine\'s Day', description: 'Romantic pink and red theme' },
  },
  'holiday-double11-03': {
    zh: { name: '双十一狂欢', description: '红橙霓虹配色，购物狂欢' },
    en: { name: 'Double 11 Sale', description: 'Vibrant red-orange, shopping festival' },
  },
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
      setError(language === 'zh' ? '加载模板失败，请稍后重试' : 'Failed to load templates');
      console.error('Failed to load templates:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Get translated template name
  const getTemplateName = (template: Template): string => {
    const translation = TEMPLATE_TRANSLATIONS[template.id];
    if (translation) {
      return translation[language].name;
    }
    return template.name;
  };

  // Get translated template description
  const getTemplateDescription = (template: Template): string => {
    const translation = TEMPLATE_TRANSLATIONS[template.id];
    if (translation) {
      return translation[language].description;
    }
    return template.prompt_modifiers.color_scheme;
  };

  const filteredTemplates =
    activeCategory === 'all'
      ? templates
      : templates.filter((tmpl) => tmpl.category === activeCategory);

  const categories: (TemplateCategory | 'all')[] = ['all', 'promotional', 'premium', 'holiday'];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-[var(--text-dark)]">
          {t.form.templateLabel} <span className="text-[var(--text-muted)] font-normal">{t.form.templateOptional}</span>
        </label>
        {selectedTemplateId && (
          <button
            type="button"
            onClick={() => onSelect(undefined)}
            disabled={disabled}
            className="text-xs text-[var(--primary)] hover:text-[var(--primary-dark)] disabled:opacity-50 transition-colors"
          >
            {t.form.clearTemplate}
          </button>
        )}
      </div>

      {/* Category Tabs */}
      <div className="flex gap-2 flex-wrap">
        {categories.map((category) => (
          <button
            key={category}
            type="button"
            onClick={() => setActiveCategory(category)}
            disabled={disabled}
            className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all duration-200 ${
              activeCategory === category
                ? 'bg-[var(--primary)] text-white'
                : 'bg-[var(--primary-bg)] text-[var(--text-muted)] hover:text-[var(--primary)]'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {t.categories[category]}
          </button>
        ))}
      </div>

      {/* Template Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="loader-spinner w-8 h-8" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center h-32 text-[var(--text-muted)]">
          <p className="text-sm">{error}</p>
          <button
            type="button"
            onClick={loadTemplates}
            className="mt-2 text-xs text-[var(--primary)] hover:underline"
          >
            {t.form.retry}
          </button>
        </div>
      ) : (
        <div className="template-scroll-container">
          <div className="grid grid-cols-2 gap-4 pt-3 pb-1">
            {filteredTemplates.map((template) => (
              <button
                key={template.id}
                type="button"
                onClick={() => onSelect(template.id)}
                disabled={disabled}
                className={`relative group rounded-lg border transition-all duration-200 text-left overflow-visible ${
                  selectedTemplateId === template.id
                    ? 'border-[var(--primary)] bg-[var(--primary-bg)] ring-1 ring-[var(--primary)]'
                    : 'border-[var(--border-light)] bg-white hover:border-[var(--primary)] hover:bg-[var(--primary-bg)]'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
                title={getTemplateDescription(template)}
              >
                {/* Category Badge - positioned outside */}
                <span
                  className={`absolute -top-2.5 right-3 px-2 py-0.5 text-[10px] font-medium text-white rounded-full z-10 shadow-sm ${
                    CATEGORY_COLORS[template.category]
                  }`}
                >
                  {t.categories[template.category]}
                </span>

                {/* Card Content - consistent padding */}
                <div className="p-3">
                  {/* Template Preview with Icon */}
                  <div className="w-full h-14 rounded-md mb-2 overflow-hidden relative bg-gradient-to-br from-[var(--primary-bg)] to-[var(--border-light)]">
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-2xl">
                        {CATEGORY_ICONS[template.category]}
                      </span>
                    </div>
                  </div>

                  {/* Template Name */}
                  <p className="text-sm font-medium text-[var(--text-dark)] truncate">{getTemplateName(template)}</p>
                  <p className="text-xs text-[var(--text-muted)] line-clamp-2 mt-1 leading-relaxed h-8">
                    {getTemplateDescription(template)}
                  </p>
                </div>

                {/* Selected Indicator */}
                {selectedTemplateId === template.id && (
                  <div className="absolute -top-2.5 left-3 w-5 h-5 bg-[var(--primary)] rounded-full flex items-center justify-center shadow-sm z-10">
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
        </div>
      )}
    </div>
  );
}

export default TemplateSelector;
