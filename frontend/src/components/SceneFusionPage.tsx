/**
 * 场景融合页面组件
 * Based on Mathilda Art Gallery Template
 * Requirements: 4.1, 4.2 - 商品图场景融合功能
 */

import { useState } from 'react';
import type { ChangeEvent } from 'react';
import { Link } from 'react-router-dom';
import type { AspectRatio, SceneFusionRequest } from '../types';
import { apiService } from '../services/api';
import { ProductImageUpload } from './ProductImageUpload';
import { AspectRatioSelector } from './AspectRatioSelector';
import { Header, Footer } from './layout';

interface SelectedImage {
  file: File;
  previewUrl: string;
}

export function SceneFusionPage() {
  // Form state
  const [selectedImage, setSelectedImage] = useState<SelectedImage | null>(null);
  const [targetScene, setTargetScene] = useState('');
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('1:1');

  // Generation state
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string>();
  const [resultImageUrl, setResultImageUrl] = useState<string>();

  const canProcess = selectedImage && targetScene.trim();

  const handleImageSelect = (file: File, previewUrl: string) => {
    setSelectedImage({ file, previewUrl });
    setResultImageUrl(undefined);
    setError(undefined);
  };

  const handleImageClear = () => {
    if (selectedImage?.previewUrl) {
      URL.revokeObjectURL(selectedImage.previewUrl);
    }
    setSelectedImage(null);
    setResultImageUrl(undefined);
  };

  const handleSceneChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setTargetScene(e.target.value);
  };

  const handleProcess = async () => {
    if (!canProcess || !selectedImage) return;

    setIsProcessing(true);
    setError(undefined);

    try {
      // First upload the image
      const uploadResult = await apiService.uploadProductImage(selectedImage.file);

      // Then request scene fusion
      const request: SceneFusionRequest = {
        product_image_url: uploadResult.url,
        target_scene: targetScene,
        aspect_ratio: aspectRatio,
      };

      const response = await apiService.sceneFusion(request);
      setResultImageUrl(response.fused_image_url);
    } catch (err) {
      console.error('Scene fusion failed:', err);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('场景融合失败，请稍后重试');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = async () => {
    if (!resultImageUrl) return;

    try {
      const response = await fetch(resultImageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'popgraph-scene-fusion.png';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
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
                场景融合
              </h2>
              <p className="text-[var(--text-muted)]">上传商品图，AI 自动生成场景背景</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 rounded-full bg-amber-100 text-amber-700 text-xs font-semibold">
                专业版功能
              </span>
            </div>
          </div>

          {/* Two Column Layout */}
          <div className="create-page-grid">
            {/* Left Sidebar - Controls */}
            <div className="create-sidebar">
              {/* Product Image Upload */}
              <div className="compact-card">
                <div className="create-section-header">
                  <h4>上传商品图</h4>
                </div>
                <ProductImageUpload
                  selectedImage={selectedImage}
                  onImageSelect={handleImageSelect}
                  onImageClear={handleImageClear}
                  disabled={isProcessing}
                />
              </div>

              {/* Target Scene Description */}
              <div className="compact-card">
                <div className="create-section-header">
                  <h4>目标场景</h4>
                </div>
                <div className="space-y-2">
                  <textarea
                    id="target-scene"
                    value={targetScene}
                    onChange={handleSceneChange}
                    disabled={isProcessing}
                    placeholder="描述您想要的场景背景，例如：现代简约的客厅，阳光透过落地窗洒进来..."
                    className="form-input min-h-[100px] resize-none"
                    aria-describedby="target-scene-hint"
                  />
                  <p id="target-scene-hint" className="text-xs text-[var(--text-muted)]">
                    详细描述目标场景，AI 将保持商品外观并融合到新背景中
                  </p>
                </div>
              </div>

              {/* Aspect Ratio */}
              <div className="compact-card">
                <div className="create-section-header">
                  <h4>输出设置</h4>
                </div>
                <AspectRatioSelector
                  value={aspectRatio}
                  onChange={setAspectRatio}
                  disabled={isProcessing}
                />
              </div>

              {/* Process Button */}
              <button
                type="button"
                onClick={handleProcess}
                disabled={!canProcess || isProcessing}
                className="btn-primary w-full flex items-center justify-center gap-2 py-4 text-lg"
              >
                {isProcessing ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>处理中...</span>
                  </>
                ) : (
                  <>
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                    <span>开始融合</span>
                  </>
                )}
              </button>

              {/* Error Message */}
              {error && (
                <div className="alert alert-error flex items-start gap-3">
                  <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="text-sm">{error}</p>
                </div>
              )}

              {/* Quick Links */}
              <div className="compact-card highlight">
                <p className="text-sm text-[var(--text-muted)] mb-3">其他创作工具</p>
                <div className="flex gap-3">
                  <Link
                    to="/create"
                    className="flex-1 px-4 py-3 bg-white rounded-lg text-center text-sm font-medium text-[var(--text-dark)] hover:shadow-md transition-shadow"
                  >
                    🎨 海报生成
                  </Link>
                  <Link
                    to="/gallery"
                    className="flex-1 px-4 py-3 bg-white rounded-lg text-center text-sm font-medium text-[var(--text-dark)] hover:shadow-md transition-shadow"
                  >
                    📁 我的作品
                  </Link>
                </div>
              </div>
            </div>

            {/* Right Main Area - Result */}
            <div className="create-main">
              <div className="compact-card h-full min-h-[500px] flex flex-col">
                <div className="flex items-center justify-between mb-6">
                  <div className="create-section-header mb-0 pb-0 border-b-0">
                    <h4>融合结果</h4>
                  </div>
                  {resultImageUrl && (
                    <button
                      type="button"
                      onClick={handleDownload}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--primary-bg)] text-[var(--primary)] text-sm font-medium hover:bg-[var(--primary)] hover:text-white transition-colors"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      下载
                    </button>
                  )}
                </div>

                {/* Result Display */}
                <div className="flex-1 flex items-center justify-center">
                  {isProcessing ? (
                    <div className="flex flex-col items-center justify-center">
                      <div className="relative">
                        <div className="w-16 h-16 border-4 border-[var(--primary-bg)] border-t-[var(--primary)] rounded-full animate-spin" />
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-2xl">🎨</span>
                        </div>
                      </div>
                      <p className="mt-4 text-[var(--text-muted)]">AI 正在融合场景...</p>
                      <p className="text-sm text-[var(--text-muted)]">预计需要 5-10 秒</p>
                    </div>
                  ) : resultImageUrl ? (
                    <div className="w-full space-y-4">
                      <div className="bg-[var(--bg-light)] rounded-lg overflow-hidden">
                        <img
                          src={resultImageUrl}
                          alt="场景融合结果"
                          className="w-full h-auto"
                        />
                      </div>
                      <p className="text-xs text-[var(--text-muted)] text-center">
                        商品已成功融合到新场景中
                      </p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center text-[var(--text-muted)]">
                      <div className="w-24 h-24 bg-[var(--primary-bg)] rounded-lg flex items-center justify-center mb-4">
                        <svg
                          className="w-12 h-12 text-[var(--primary)]"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                          />
                        </svg>
                      </div>
                      <p className="text-center">上传商品图并描述目标场景</p>
                      <p className="text-sm mt-1">AI 将自动完成场景融合</p>
                    </div>
                  )}
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

export default SceneFusionPage;
