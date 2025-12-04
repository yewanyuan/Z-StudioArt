/**
 * 场景融合页面组件
 * Requirements: 4.1, 4.2 - 商品图场景融合功能
 */

import { useState } from 'react';
import type { ChangeEvent } from 'react';
import type { AspectRatio, SceneFusionRequest } from '../types';
import { apiService } from '../services/api';
import { ProductImageUpload } from './ProductImageUpload';
import { AspectRatioSelector } from './AspectRatioSelector';

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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">场景融合</h1>
              <p className="text-sm text-gray-400">上传商品图，AI 自动生成场景背景</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-amber-600 text-white text-xs font-medium rounded-full">
                专业版功能
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Panel - Input */}
          <div className="space-y-6">
            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <h2 className="text-lg font-semibold text-white mb-6">上传商品图</h2>

              <div className="space-y-6">
                {/* Product Image Upload */}
                <ProductImageUpload
                  selectedImage={selectedImage}
                  onImageSelect={handleImageSelect}
                  onImageClear={handleImageClear}
                  disabled={isProcessing}
                />

                {/* Target Scene Description */}
                <div className="space-y-2">
                  <label
                    htmlFor="target-scene"
                    className="block text-sm font-medium text-gray-200"
                  >
                    目标场景描述
                  </label>
                  <textarea
                    id="target-scene"
                    value={targetScene}
                    onChange={handleSceneChange}
                    disabled={isProcessing}
                    placeholder="描述您想要的场景背景，例如：现代简约的客厅，阳光透过落地窗洒进来..."
                    className="w-full h-32 px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-describedby="target-scene-hint"
                  />
                  <p id="target-scene-hint" className="text-xs text-gray-400">
                    详细描述目标场景，AI 将保持商品外观并融合到新背景中
                  </p>
                </div>

                {/* Aspect Ratio */}
                <AspectRatioSelector
                  value={aspectRatio}
                  onChange={setAspectRatio}
                  disabled={isProcessing}
                />

                {/* Process Button */}
                <button
                  type="button"
                  onClick={handleProcess}
                  disabled={!canProcess || isProcessing}
                  className="w-full py-4 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {isProcessing ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                      处理中...
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
                      开始融合
                    </>
                  )}
                </button>

                {/* Error Message */}
                {error && (
                  <div className="p-4 bg-red-900/50 border border-red-700 rounded-lg">
                    <p className="text-sm text-red-300">{error}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Panel - Result */}
          <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-white">融合结果</h2>
              {resultImageUrl && (
                <button
                  type="button"
                  onClick={handleDownload}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
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
            {isProcessing ? (
              <div className="flex flex-col items-center justify-center h-80">
                <div className="relative">
                  <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-600 border-t-red-500" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl">🎨</span>
                  </div>
                </div>
                <p className="mt-4 text-gray-400">AI 正在融合场景...</p>
                <p className="text-sm text-gray-500">预计需要 5-10 秒</p>
              </div>
            ) : resultImageUrl ? (
              <div className="space-y-4">
                <div className="bg-gray-700 rounded-lg overflow-hidden">
                  <img
                    src={resultImageUrl}
                    alt="场景融合结果"
                    className="w-full h-auto"
                  />
                </div>
                <p className="text-xs text-gray-500 text-center">
                  商品已成功融合到新场景中
                </p>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-80 text-gray-400">
                <div className="w-24 h-24 bg-gray-700 rounded-lg flex items-center justify-center mb-4">
                  <svg
                    className="w-12 h-12 text-gray-500"
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
                <p className="text-sm text-gray-500 mt-1">AI 将自动完成场景融合</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default SceneFusionPage;
