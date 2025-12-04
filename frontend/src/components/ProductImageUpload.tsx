/**
 * 商品图上传组件
 * Requirements: 4.1, 4.2 - 支持商品白底图上传和场景描述输入
 */

import { useState, useRef } from 'react';
import type { ChangeEvent, DragEvent } from 'react';

interface ProductImageUploadProps {
  onImageSelect: (file: File, previewUrl: string) => void;
  onImageClear: () => void;
  selectedImage?: { file: File; previewUrl: string } | null;
  disabled?: boolean;
}

export function ProductImageUpload({
  onImageSelect,
  onImageClear,
  selectedImage,
  disabled = false,
}: ProductImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string>();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
  const MAX_SIZE_MB = 10;

  const validateFile = (file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return '请上传 JPG、PNG 或 WebP 格式的图片';
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `图片大小不能超过 ${MAX_SIZE_MB}MB`;
    }
    return null;
  };

  const handleFile = (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(undefined);
    const previewUrl = URL.createObjectURL(file);
    onImageSelect(file, previewUrl);
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  const handleClear = () => {
    if (selectedImage?.previewUrl) {
      URL.revokeObjectURL(selectedImage.previewUrl);
    }
    onImageClear();
    setError(undefined);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-200">商品图片</label>

      {/* Upload Area */}
      {!selectedImage ? (
        <div
          onClick={handleClick}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-red-500 bg-red-500/10'
              : 'border-gray-600 hover:border-gray-500 bg-gray-800/50'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES.join(',')}
            onChange={handleFileChange}
            disabled={disabled}
            className="hidden"
            aria-label="上传商品图片"
          />

          <div className="flex flex-col items-center">
            <div className="w-16 h-16 bg-gray-700 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-gray-400"
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
            <p className="text-gray-300 mb-1">
              {isDragging ? '松开鼠标上传' : '点击或拖拽上传商品图'}
            </p>
            <p className="text-xs text-gray-500">
              支持 JPG、PNG、WebP，最大 {MAX_SIZE_MB}MB
            </p>
            <p className="text-xs text-gray-500 mt-1">建议使用白底商品图效果更佳</p>
          </div>
        </div>
      ) : (
        /* Preview Area */
        <div className="relative bg-gray-800 rounded-lg overflow-hidden">
          <div className="aspect-square relative">
            <img
              src={selectedImage.previewUrl}
              alt="商品预览"
              className="w-full h-full object-contain bg-white"
            />

            {/* Overlay with actions */}
            <div className="absolute inset-0 bg-black/40 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
              <button
                type="button"
                onClick={handleClick}
                disabled={disabled}
                className="p-3 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
                title="更换图片"
              >
                <svg
                  className="w-5 h-5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              </button>
              <button
                type="button"
                onClick={handleClear}
                disabled={disabled}
                className="p-3 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
                title="删除图片"
              >
                <svg
                  className="w-5 h-5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* File info */}
          <div className="p-3 border-t border-gray-700">
            <p className="text-sm text-gray-300 truncate">{selectedImage.file.name}</p>
            <p className="text-xs text-gray-500">
              {(selectedImage.file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>

          {/* Hidden file input for replacement */}
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES.join(',')}
            onChange={handleFileChange}
            disabled={disabled}
            className="hidden"
            aria-label="更换商品图片"
          />
        </div>
      )}

      {/* Error Message */}
      {error && (
        <p className="text-sm text-red-400" role="alert">
          {error}
        </p>
      )}

      {/* Hint */}
      <p className="text-xs text-gray-400">
        上传商品白底图，AI 将自动提取商品主体并融合到新场景中
      </p>
    </div>
  );
}

export default ProductImageUpload;
