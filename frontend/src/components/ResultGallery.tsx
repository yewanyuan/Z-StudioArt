import { useState } from 'react';
import { createPortal } from 'react-dom';
import type { GeneratedImage, AspectRatio, Language } from '../types';
import { TRANSLATIONS } from '../constants/locales';

interface ResultGalleryProps {
  images: GeneratedImage[];
  isLoading: boolean;
  aspectRatio: AspectRatio;
  language: Language;
}

export function ResultGallery({ images, isLoading, aspectRatio, language }: ResultGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const t = TRANSLATIONS[language].gallery;

  const getAspectClass = () => {
    switch (aspectRatio) {
      case '1:1':
        return 'aspect-square';
      case '9:16':
        return 'aspect-[9/16]';
      case '16:9':
        return 'aspect-video';
      default:
        return 'aspect-square';
    }
  };

  const handleDownload = async (image: GeneratedImage, index: number) => {
    try {
      const response = await fetch(image.url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `popgraph-poster-${index + 1}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleDownloadAll = async () => {
    for (let i = 0; i < images.length; i++) {
      await handleDownload(images[i], i);
      // Small delay between downloads
      await new Promise((resolve) => setTimeout(resolve, 300));
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px]">
        <div className="relative">
          <div className="absolute inset-0 bg-indigo-500 blur-xl opacity-20 animate-pulse rounded-full" />
          <div className="relative animate-spin rounded-full h-16 w-16 border-4 border-white/10 border-t-indigo-500" />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl animate-bounce">🎨</span>
          </div>
        </div>
        <p className="mt-6 text-lg font-medium text-white">{t.loadingTitle}</p>
        <p className="text-sm text-gray-400">{t.loadingDesc}</p>
      </div>
    );
  }

  // Empty state
  if (images.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-gray-500">
        <div className="w-24 h-24 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center mb-6 transform rotate-3 transition-transform hover:rotate-0 duration-300">
          <svg
            className="w-10 h-10 text-gray-600"
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
        <p className="text-lg font-medium text-gray-400">{t.emptyTitle}</p>
        <p className="text-sm text-gray-600 mt-1">{t.emptyDesc}</p>
      </div>
    );
  }

  // Results grid
  return (
    <div className="space-y-4 animate-in fade-in duration-500">
      {/* Download All Button */}
      {images.length > 1 && (
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleDownloadAll}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-gray-300 hover:text-white text-xs font-medium rounded-full transition-all"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            {t.downloadAll} ({images.length})
          </button>
        </div>
      )}

      {/* Image Grid */}
      <div
        className={`grid gap-4 ${
          images.length === 1 ? 'grid-cols-1' : 'grid-cols-2'
        }`}
      >
        {images.map((image, index) => (
          <div
            key={image.id}
            className="group relative bg-black/40 rounded-2xl overflow-hidden border border-white/10 shadow-2xl transition-all hover:border-indigo-500/50 hover:shadow-indigo-500/10"
          >
            {/* Image */}
            <div className={getAspectClass()}>
              <img
                src={image.thumbnail_url || image.url}
                alt={`Generated Poster ${index + 1}`}
                className="w-full h-full object-cover cursor-pointer transition-transform duration-700 group-hover:scale-105"
                onClick={() => setSelectedIndex(index)}
              />
            </div>

            {/* Watermark Badge */}
            {image.has_watermark && (
              <div className="absolute top-3 left-3 px-2 py-1 bg-black/50 backdrop-blur-md border border-white/10 rounded text-[10px] font-medium text-gray-300 uppercase tracking-wider">
                {t.watermark}
              </div>
            )}

            {/* Hover Overlay */}
            <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center gap-4">
              <button
                type="button"
                onClick={() => setSelectedIndex(index)}
                className="p-3 bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 rounded-full transition-all transform hover:scale-110 text-white"
                title="View Fullscreen"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"
                  />
                </svg>
              </button>
              <button
                type="button"
                onClick={() => handleDownload(image, index)}
                className="p-3 bg-indigo-600/80 hover:bg-indigo-600 backdrop-blur-md border border-indigo-500/50 rounded-full transition-all transform hover:scale-110 text-white shadow-lg shadow-indigo-500/30"
                title="Download"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
              </button>
            </div>

            {/* Image Number */}
            <div className="absolute bottom-3 right-3 w-6 h-6 bg-black/60 backdrop-blur rounded-full flex items-center justify-center border border-white/10">
              <span className="text-xs text-white font-medium">{index + 1}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Dimensions Info */}
      {images.length > 0 && (
        <p className="text-[10px] text-gray-500 text-center uppercase tracking-widest">
          {t.dimensions}: {images[0].width} × {images[0].height} px
        </p>
      )}

      {/* Lightbox Modal */}
      {selectedIndex !== null && createPortal(
        <div
          className="fixed inset-0 z-50 bg-slate-900/95 backdrop-blur-xl flex items-center justify-center p-4"
          onClick={() => setSelectedIndex(null)}
        >
          <div className="relative w-full h-full max-w-6xl flex flex-col items-center justify-center">
            {/* Close Button */}
            <button
              type="button"
              onClick={() => setSelectedIndex(null)}
              className="absolute top-4 right-4 p-2 text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>

            {/* Full Image */}
            <img
              src={images[selectedIndex].url}
              alt={`Generated Poster ${selectedIndex + 1}`}
              className="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />

            {/* Navigation */}
            {images.length > 1 && (
              <>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedIndex((selectedIndex - 1 + images.length) % images.length);
                  }}
                  className="absolute left-4 top-1/2 -translate-y-1/2 p-4 bg-black/20 hover:bg-black/40 backdrop-blur rounded-full text-white transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 19l-7-7 7-7"
                    />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedIndex((selectedIndex + 1) % images.length);
                  }}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-4 bg-black/20 hover:bg-black/40 backdrop-blur rounded-full text-white transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
              </>
            )}

            {/* Download Button */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDownload(images[selectedIndex], selectedIndex);
                }}
                className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full shadow-lg shadow-indigo-500/30 transition-all transform hover:-translate-y-0.5 font-medium"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                {t.downloadImage}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

export default ResultGallery;
