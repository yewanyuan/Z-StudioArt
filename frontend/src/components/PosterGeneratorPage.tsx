/**
 * 海报生成页面组件
 * Based on Mathilda Art Gallery Template
 * 整合场景描述、文案输入、模板选择、尺寸选择
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import type {
  AspectRatio,
  PosterGenerationRequest,
  GeneratedImage,
} from '../types';
import { apiService } from '../services/api';
import { useLanguageStore } from '../stores/languageStore';
import { SceneDescriptionInput } from './SceneDescriptionInput';
import { MarketingTextInput } from './MarketingTextInput';
import { TemplateSelector } from './TemplateSelector';
import { AspectRatioSelector } from './AspectRatioSelector';
import { ResultGallery } from './ResultGallery';
import { Header, Footer } from './layout';
import { TRANSLATIONS } from '../constants/locales';

export function PosterGeneratorPage() {
  // Get language from global store
  const { language } = useLanguageStore();

  // Form state
  const [sceneDescription, setSceneDescription] = useState('');
  const [marketingText, setMarketingText] = useState('');
  const [templateId, setTemplateId] = useState<string | undefined>();
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('1:1');
  const [customWidth, setCustomWidth] = useState(1024);
  const [customHeight, setCustomHeight] = useState(1024);

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string>();
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([]);

  const canGenerate = sceneDescription.trim() && marketingText.trim();
  const t = TRANSLATIONS[language];

  const handleCustomDimensionsChange = (width: number, height: number) => {
    setCustomWidth(width);
    setCustomHeight(height);
  };

  const handleGenerate = async () => {
    if (!canGenerate) return;

    setIsGenerating(true);
    setError(undefined);

    try {
      const request: PosterGenerationRequest = {
        scene_description: sceneDescription,
        marketing_text: marketingText,
        language,
        template_id: templateId,
        aspect_ratio: aspectRatio,
        custom_width: aspectRatio === 'custom' ? customWidth : undefined,
        custom_height: aspectRatio === 'custom' ? customHeight : undefined,
        batch_size: 1,
      };

      const response = await apiService.generatePoster(request);
      setGeneratedImages(response.images);
    } catch (err) {
      console.error('Generation failed:', err);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('生成失败，请稍后重试');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleClearResults = () => {
    setGeneratedImages([]);
    setError(undefined);
  };

  return (
    <div className="page-wrapper">
      {/* Background Curve */}
      <div className="bg-curve" />

      {/* Header */}
      <Header />

      {/* Main Content */}
      <main className="main-content py-8">
        <div className="container-main">
          {/* Page Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <h2 className="text-2xl lg:text-3xl font-bold text-[var(--primary)] mb-2">
                {t.header.title}
              </h2>
              <p className="text-[var(--text-muted)]">{t.header.subtitle}</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 border border-green-200">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs font-medium text-green-700">{t.header.systemStatus}</span>
              </div>
              <span className="px-3 py-1.5 rounded-full bg-[var(--primary-bg)] text-[var(--primary)] text-xs font-semibold">
                {t.header.plan}
              </span>
            </div>
          </div>

          {/* Two Column Layout */}
          <div className="create-page-grid">
            {/* Left Sidebar - Controls */}
            <div className="create-sidebar">
              {/* Scene & Marketing Inputs */}
              <div className="compact-card">
                <div className="create-section-header">
                  <h4>{t.form.title}</h4>
                </div>

                <div className="space-y-5">
                  {/* Scene Description */}
                  <SceneDescriptionInput
                    value={sceneDescription}
                    onChange={setSceneDescription}
                    language={language}
                    disabled={isGenerating}
                  />

                  {/* Marketing Text */}
                  <MarketingTextInput
                    value={marketingText}
                    onChange={setMarketingText}
                    language={language}
                    disabled={isGenerating}
                  />
                </div>
              </div>

              {/* Aspect Ratio */}
              <div className="compact-card">
                <div className="create-section-header">
                  <h4>{language === 'zh' ? '输出设置' : 'Output Settings'}</h4>
                </div>
                <AspectRatioSelector
                  value={aspectRatio}
                  onChange={setAspectRatio}
                  customWidth={customWidth}
                  customHeight={customHeight}
                  onCustomChange={handleCustomDimensionsChange}
                  language={language}
                  disabled={isGenerating}
                />
              </div>

              {/* Template Selector */}
              <div className="compact-card">
                <div className="create-section-header">
                  <h4>{language === 'zh' ? '风格模板' : 'Style Templates'}</h4>
                </div>
                <TemplateSelector
                  selectedTemplateId={templateId}
                  onSelect={setTemplateId}
                  language={language}
                  disabled={isGenerating}
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="alert alert-error flex items-start gap-3">
                  <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="text-sm">{error}</p>
                </div>
              )}
            </div>

            {/* Right Main Area - Results */}
            <div className="create-main flex flex-col gap-6">
              {/* Results Area */}
              <div className="compact-card flex-1 flex flex-col min-h-[420px]">
                <div className="flex items-center justify-between mb-4">
                  <div className="create-section-header mb-0 pb-0 border-b-0">
                    <h4>{t.gallery.title}</h4>
                  </div>
                  {generatedImages.length > 0 && (
                    <button
                      type="button"
                      onClick={handleClearResults}
                      className="text-sm px-4 py-2 rounded-lg bg-[var(--primary-bg)] text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors"
                    >
                      {t.gallery.clearAll}
                    </button>
                  )}
                </div>

                <div className="flex-1">
                  <ResultGallery
                    images={generatedImages}
                    isLoading={isGenerating}
                    aspectRatio={aspectRatio}
                    language={language}
                  />
                </div>
              </div>

              {/* Bottom Action Bar - Generate Button & Quick Links */}
              <div className="compact-card">
                <div className="flex flex-col lg:flex-row gap-4 items-stretch lg:items-center">
                  {/* Generate Button */}
                  <button
                    type="button"
                    onClick={handleGenerate}
                    disabled={!canGenerate || isGenerating}
                    className="generate-btn flex-1 lg:flex-none lg:min-w-[200px]"
                  >
                    {isGenerating ? (
                      <>
                        <div className="generate-btn-spinner" />
                        <span>{t.form.generatingBtn}</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span>{t.form.generateBtn}</span>
                      </>
                    )}
                  </button>

                  {/* Divider */}
                  <div className="hidden lg:block w-px h-10 bg-[var(--border-light)]" />

                  {/* Quick Links */}
                  <div className="flex items-center gap-3 flex-1">
                    <span className="text-sm text-[var(--text-muted)] whitespace-nowrap">
                      {language === 'zh' ? '其他工具' : 'Other Tools'}:
                    </span>
                    <Link
                      to="/scene-fusion"
                      className="flex items-center gap-2 px-4 py-2.5 bg-[var(--primary-bg)] rounded-lg text-sm font-medium text-[var(--text-dark)] hover:bg-[var(--primary)] hover:text-white transition-all"
                    >
                      <span>🖼️</span>
                      <span>{language === 'zh' ? '场景融合' : 'Scene Fusion'}</span>
                    </Link>
                    <Link
                      to="/gallery"
                      className="flex items-center gap-2 px-4 py-2.5 bg-[var(--primary-bg)] rounded-lg text-sm font-medium text-[var(--text-dark)] hover:bg-[var(--primary)] hover:text-white transition-all"
                    >
                      <span>📁</span>
                      <span>{language === 'zh' ? '我的作品' : 'My Works'}</span>
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}

export default PosterGeneratorPage;
