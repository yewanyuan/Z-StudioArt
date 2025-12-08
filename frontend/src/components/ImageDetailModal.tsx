/**
 * 图片详情模态框组件
 * Requirements: 9.3, 9.4
 * 
 * 功能：
 * - 显示大图
 * - 显示生成参数
 * - 下载功能
 */

import { useState } from 'react';
import type { HistoryDetailResponse } from '../types';

interface ImageDetailModalProps {
  isOpen: boolean;
  isLoading: boolean;
  item: HistoryDetailResponse | null;
  onClose: () => void;
  onDelete: (id: string) => void;
  formatDate: (date: string) => string;
  getTypeLabel: (type: string) => string;
}

export function ImageDetailModal({
  isOpen,
  isLoading,
  item,
  onClose,
  onDelete,
  formatDate,
  getTypeLabel,
}: ImageDetailModalProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);

  if (!isOpen) return null;

  /**
   * 下载图片
   */
  const handleDownload = async (url: string, index: number) => {
    setIsDownloading(true);
    
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `popgraph-${item?.id || 'image'}-${index + 1}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error('Download failed:', err);
      // 如果 fetch 失败，尝试直接打开链接
      window.open(url, '_blank');
    } finally {
      setIsDownloading(false);
    }
  };

  /**
   * 下载所有图片
   */
  const handleDownloadAll = async () => {
    if (!item?.output_urls.length) return;
    
    for (let i = 0; i < item.output_urls.length; i++) {
      await handleDownload(item.output_urls[i], i);
      // 添加延迟避免浏览器阻止多次下载
      if (i < item.output_urls.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  };

  /**
   * 格式化参数显示
   */
  const formatParams = (params: Record<string, unknown>): { label: string; value: string }[] => {
    const result: { label: string; value: string }[] = [];
    
    const labelMap: Record<string, string> = {
      scene_description: '场景描述',
      marketing_text: '营销文案',
      template_id: '模板',
      aspect_ratio: '宽高比',
      batch_size: '生成数量',
      language: '语言',
      target_scene: '目标场景',
      product_image_url: '商品图片',
    };

    for (const [key, value] of Object.entries(params)) {
      if (value !== null && value !== undefined && value !== '') {
        const label = labelMap[key] || key;
        let displayValue = String(value);
        
        // 特殊处理某些值
        if (key === 'language') {
          displayValue = value === 'zh' ? '中文' : '英文';
        } else if (key === 'product_image_url') {
          displayValue = '已上传';
        }
        
        result.push({ label, value: displayValue });
      }
    }
    
    return result;
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      onClick={onClose}
    >
      <div 
        className="bg-gray-900 rounded-xl max-w-5xl w-full mx-4 max-h-[90vh] overflow-hidden border border-gray-700 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-medium text-white">图片详情</h2>
            {item && (
              <span className={`text-xs px-2 py-0.5 rounded ${
                item.type === 'poster' 
                  ? 'bg-indigo-500/20 text-indigo-300' 
                  : 'bg-emerald-500/20 text-emerald-300'
              }`}>
                {getTypeLabel(item.type)}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 内容区 */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="flex flex-col items-center gap-4">
                <div className="animate-spin rounded-full h-12 w-12 border-2 border-indigo-500/30 border-t-indigo-500" />
                <span className="text-gray-400">加载中...</span>
              </div>
            </div>
          ) : item ? (
            <div className="flex flex-col lg:flex-row">
              {/* 左侧：图片展示 */}
              <div className="lg:w-2/3 p-4">
                {/* 主图 */}
                <div className="relative bg-gray-800 rounded-lg overflow-hidden">
                  {item.output_urls.length > 0 ? (
                    <img
                      src={item.output_urls[currentImageIndex]}
                      alt={`生成图片 ${currentImageIndex + 1}`}
                      className="w-full h-auto max-h-[60vh] object-contain"
                    />
                  ) : (
                    <div className="aspect-video flex items-center justify-center">
                      <span className="text-gray-500">图片不可用</span>
                    </div>
                  )}
                  
                  {/* 水印标识 */}
                  {item.has_watermark && (
                    <div className="absolute top-2 right-2 px-2 py-1 bg-black/50 rounded text-xs text-gray-300">
                      含水印
                    </div>
                  )}
                </div>

                {/* 缩略图列表（多图时显示） */}
                {item.output_urls.length > 1 && (
                  <div className="mt-4 flex gap-2 overflow-x-auto pb-2">
                    {item.output_urls.map((url, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentImageIndex(index)}
                        className={`flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 transition-colors ${
                          index === currentImageIndex
                            ? 'border-indigo-500'
                            : 'border-transparent hover:border-gray-600'
                        }`}
                      >
                        <img
                          src={url}
                          alt={`缩略图 ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                      </button>
                    ))}
                  </div>
                )}

                {/* 下载按钮 */}
                <div className="mt-4 flex gap-3">
                  <button
                    onClick={() => handleDownload(item.output_urls[currentImageIndex], currentImageIndex)}
                    disabled={isDownloading || !item.output_urls.length}
                    className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {isDownloading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" />
                        下载中...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        下载当前图片
                      </>
                    )}
                  </button>
                  
                  {item.output_urls.length > 1 && (
                    <button
                      onClick={handleDownloadAll}
                      disabled={isDownloading}
                      className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                      下载全部
                    </button>
                  )}
                </div>
              </div>

              {/* 右侧：参数信息 */}
              <div className="lg:w-1/3 p-4 border-t lg:border-t-0 lg:border-l border-gray-700">
                <h3 className="text-sm font-medium text-gray-400 mb-4">生成信息</h3>
                
                {/* 基本信息 */}
                <div className="space-y-3 mb-6">
                  <div className="flex justify-between">
                    <span className="text-gray-500">创建时间</span>
                    <span className="text-gray-300">{formatDate(item.created_at)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">处理耗时</span>
                    <span className="text-gray-300">{(item.processing_time_ms / 1000).toFixed(1)}秒</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">图片数量</span>
                    <span className="text-gray-300">{item.output_urls.length}张</span>
                  </div>
                </div>

                {/* 生成参数 */}
                <h3 className="text-sm font-medium text-gray-400 mb-4">生成参数</h3>
                <div className="space-y-3">
                  {formatParams(item.input_params).map(({ label, value }) => (
                    <div key={label}>
                      <span className="text-xs text-gray-500 block mb-1">{label}</span>
                      <p className="text-sm text-gray-300 break-words">{value}</p>
                    </div>
                  ))}
                </div>

                {/* 删除按钮 */}
                <div className="mt-8 pt-4 border-t border-gray-700">
                  <button
                    onClick={() => onDelete(item.id)}
                    className="w-full px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    删除记录
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center py-20">
              <span className="text-gray-500">无法加载详情</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ImageDetailModal;
