/**
 * 海报生成页面组件
 * Requirements: 1.1, 3.1, 5.1, 5.2, 5.3
 * 整合场景描述、文案输入、模板选择、尺寸选择
 */

import { useState } from 'react';
import type {
  AspectRatio,
  Language,
  PosterGenerationRequest,
  GeneratedImage,
} from '../types';
import { apiService } from '../services/api';
import { SceneDescriptionInput } from './SceneDescriptionInput';
import { MarketingTextInput } from './MarketingTextInput';
import { TemplateSelector } from './TemplateSelector';
import { AspectRatioSelector } from './AspectRatioSelector';
import { ResultGallery } from './ResultGallery';
import { TRANSLATIONS } from '../constants/locales';

export function PosterGeneratorPage() {
  // Form state
  const [sceneDescription, setSceneDescription] = useState('');
  const [marketingText, setMarketingText] = useState('');
  const [language, setLanguage] = useState<Language>('zh');
  const [templateId, setTemplateId] = useState<string | undefined>();
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('1:1');
  const [customWidth, setCustomWidth] = useState(1024);
  const [customHeight, setCustomHeight] = useState(1024);
  // const [batchMode, setBatchMode] = useState(false);

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
        batch_size: 1, // batchMode disabled
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
    <div className="min-h-screen bg-[#0f172a] bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.3),rgba(255,255,255,0))] text-white selection:bg-indigo-500/30">
      {/* Header */}
      <header className="border-b border-white/10 bg-slate-900/50 backdrop-blur-xl sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">{t.header.title} <span className="font-light text-indigo-300">{t.header.subtitle}</span></h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-xs font-medium text-gray-300">{t.header.systemStatus}</span>
            </div>
            <span className="text-xs font-medium px-3 py-1.5 rounded-full bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 text-indigo-300">
              {t.header.plan}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Panel - Input Form */}
          <div className="lg:col-span-5 space-y-6">
            {/* Control Panel */}
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 shadow-2xl shadow-black/20">
              <div className="flex items-center gap-2 mb-6">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span className="w-1 h-6 rounded-full bg-indigo-500" />
                  {t.form.title}
                </h2>
              </div>

              <div className="space-y-6">
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
                  onLanguageChange={setLanguage}
                  disabled={isGenerating}
                />

                {/* Aspect Ratio */}
                <AspectRatioSelector
                  value={aspectRatio}
                  onChange={setAspectRatio}
                  customWidth={customWidth}
                  customHeight={customHeight}
                  onCustomChange={handleCustomDimensionsChange}
                  language={language}
                  disabled={isGenerating}
                />

                {/* Batch Mode Toggle - 暂时禁用，API 限流导致批量生成不稳定 */}
                {/* <div className="group flex items-center justify-between p-4 bg-black/20 rounded-xl border border-white/5 hover:border-white/10 transition-colors">
                  <div>
                    <p className="text-sm font-medium text-gray-200 group-hover:text-white transition-colors">{t.form.previewMode}</p>
                    <p className="text-xs text-gray-400">{t.form.previewDesc}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setBatchMode(!batchMode)}
                    disabled={isGenerating}
                    className={`relative w-12 h-6 rounded-full transition-all duration-300 ${
                      batchMode ? 'bg-indigo-600 shadow-[0_0_12px_rgba(79,70,229,0.5)]' : 'bg-white/10'
                    } disabled:opacity-50`}
                    role="switch"
                    aria-checked={batchMode}
                  >
                    <span
                      className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform duration-300 shadow-sm ${
                        batchMode ? 'translate-x-6' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div> */}

                {/* Generate Button */}
                <button
                  type="button"
                  onClick={handleGenerate}
                  disabled={!canGenerate || isGenerating}
                  className="relative w-full group overflow-hidden rounded-xl p-[1px] focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-70"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 opacity-80 group-hover:opacity-100 transition-opacity" />
                  <div className="relative bg-slate-900/50 h-full w-full rounded-xl flex items-center justify-center gap-2 py-3.5 transition-colors group-hover:bg-transparent">
                    {isGenerating ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white" />
                        <span className="font-semibold text-white">{t.form.generatingBtn}</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span className="font-semibold text-white">{t.form.generateBtn}</span>
                      </>
                    )}
                  </div>
                </button>

                {/* Error Message */}
                {error && (
                  <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3">
                    <svg className="w-5 h-5 text-red-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <p className="text-sm text-red-200">{error}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Template Selector */}
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 shadow-xl">
              <TemplateSelector
                selectedTemplateId={templateId}
                onSelect={setTemplateId}
                language={language}
                disabled={isGenerating}
              />
            </div>
          </div>

          {/* Right Panel - Results */}
          <div className="lg:col-span-7">
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 shadow-2xl h-full min-h-[600px] flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span className="w-1 h-6 rounded-full bg-purple-500" />
                  {t.gallery.title}
                </h2>
                {generatedImages.length > 0 && (
                  <button
                    type="button"
                    onClick={handleClearResults}
                    className="text-xs px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors border border-white/5 hover:border-white/10"
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
          </div>
        </div>
      </main>
    </div>
  );
}

export default PosterGeneratorPage;
