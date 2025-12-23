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

  // Modal state for viewing large image
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalImageIndex, setModalImageIndex] = useState(0);

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

  // View large image
  const handleViewImage = () => {
    if (generatedImages.length > 0) {
      setModalImageIndex(0);
      setIsModalOpen(true);
    }
  };

  // Download first image
  const handleDownloadImage = async () => {
    if (generatedImages.length > 0) {
      const image = generatedImages[0];
      try {
        const response = await fetch(image.url);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `popgraph-poster-1.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Download failed:', error);
      }
    }
  };

  // Close modal
  const closeModal = () => {
    setIsModalOpen(false);
  };

  // Download from modal
  const handleModalDownload = async () => {
    if (generatedImages.length > modalImageIndex) {
      const image = generatedImages[modalImageIndex];
      try {
        const response = await fetch(image.url);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `popgraph-poster-${modalImageIndex + 1}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Download failed:', error);
      }
    }
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
            {/* Left Column */}
            <div className="create-sidebar">
              {/* Scene & Marketing Inputs (Create Poster) */}
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

              {/* Style Templates - moved below Create Poster */}
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

            {/* Right Column */}
            <div className="create-main flex flex-col gap-6">
              {/* Gallery Area - Fixed height, images shown as thumbnails */}
              <div className="compact-card flex flex-col" style={{ height: '580px' }}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                  <div className="create-section-header mb-0 pb-0 border-b-0">
                    <h4>{t.gallery.title}</h4>
                  </div>
                  {generatedImages.length > 0 && (
                    <div className="flex items-center gap-2 flex-wrap">
                      {/* View Button */}
                      <button
                        type="button"
                        onClick={handleViewImage}
                        className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg bg-[var(--primary)] text-white hover:bg-[var(--primary-dark)] transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        <span className="sr-only sm:not-sr-only">{language === 'zh' ? '查看' : 'View'}</span>
                      </button>

                      {/* Download Button */}
                      <button
                        type="button"
                        onClick={handleDownloadImage}
                        className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        <span className="sr-only sm:not-sr-only">{language === 'zh' ? '下载' : 'Download'}</span>
                      </button>

                      {/* Spacer/Divider - hidden on mobile */}
                      <div className="hidden sm:block w-px h-6 bg-[var(--border-light)] mx-1" />

                      {/* Clear All Button */}
                      <button
                        type="button"
                        onClick={handleClearResults}
                        className="text-sm px-3 py-2 rounded-lg bg-[var(--primary-bg)] text-[var(--text-muted)] hover:text-red-500 hover:bg-red-50 transition-colors"
                      >
                        {t.gallery.clearAll}
                      </button>
                    </div>
                  )}
                </div>

                <div className="flex-1 overflow-hidden">
                  <ResultGallery
                    images={generatedImages}
                    isLoading={isGenerating}
                    aspectRatio={aspectRatio}
                    language={language}
                  />
                </div>
              </div>

              {/* Bottom Row: Output Settings + Generate Button & Quick Links */}
              <div className="flex flex-col lg:flex-row gap-6">
                {/* Output Settings - separate card */}
                <div className="compact-card flex-1">
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

                {/* Generate Button & Quick Links - separate card on the right */}
                <div className="compact-card lg:w-[200px] flex flex-col justify-between">
                  {/* Generate Button */}
                  <button
                    type="button"
                    onClick={handleGenerate}
                    disabled={!canGenerate || isGenerating}
                    className="generate-btn w-full"
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

                  {/* Quick Links */}
                  <div className="flex flex-col gap-2 mt-4">
                    <span className="text-xs text-[var(--text-muted)]">
                      {language === 'zh' ? '其他工具' : 'Other Tools'}
                    </span>
                    <Link
                      to="/scene-fusion"
                      className="flex items-center gap-2 px-3 py-2 bg-[var(--primary-bg)] rounded-lg text-sm font-medium text-[var(--text-dark)] hover:bg-[var(--primary)] hover:text-white transition-all"
                    >
                      <span>🖼️</span>
                      <span>{language === 'zh' ? '场景融合' : 'Scene Fusion'}</span>
                    </Link>
                    <Link
                      to="/gallery"
                      className="flex items-center gap-2 px-3 py-2 bg-[var(--primary-bg)] rounded-lg text-sm font-medium text-[var(--text-dark)] hover:bg-[var(--primary)] hover:text-white transition-all"
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

      {/* Image View Modal */}
      {isModalOpen && generatedImages.length > 0 && (
        <div
          className="fixed inset-0 z-[9999] bg-black/90 flex justify-center items-center"
          onClick={closeModal}
        >
          <div
            className="relative max-w-[90%] max-h-[90%] bg-transparent p-2"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              type="button"
              className="absolute -top-10 right-0 bg-transparent border-none text-3xl text-white cursor-pointer z-10 hover:text-gray-300"
              onClick={closeModal}
            >
              &times;
            </button>

            {/* Large Image */}
            <img
              src={generatedImages[modalImageIndex].url}
              alt={`Generated Poster ${modalImageIndex + 1}`}
              className="block max-w-full max-h-[80vh] w-auto h-auto rounded-lg"
            />

            {/* Bottom Controls */}
            <div className="mt-4 flex items-center justify-center gap-4">
              {/* Previous Button */}
              {generatedImages.length > 1 && (
                <button
                  type="button"
                  onClick={() => setModalImageIndex((modalImageIndex - 1 + generatedImages.length) % generatedImages.length)}
                  className="p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
              )}

              {/* Download Button */}
              <button
                type="button"
                onClick={handleModalDownload}
                className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full shadow-lg transition-all font-medium"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                {language === 'zh' ? '下载图片' : 'Download'}
              </button>

              {/* Next Button */}
              {generatedImages.length > 1 && (
                <button
                  type="button"
                  onClick={() => setModalImageIndex((modalImageIndex + 1) % generatedImages.length)}
                  className="p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              )}
            </div>

            {/* Image Counter */}
            {generatedImages.length > 1 && (
              <p className="mt-3 text-white/50 text-sm text-center">
                {modalImageIndex + 1} / {generatedImages.length}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default PosterGeneratorPage;
