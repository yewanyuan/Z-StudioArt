/**
 * 历史记录页面
 * Requirements: 9.1, 9.2
 * 
 * 功能：
 * - 缩略图网格布局展示生成历史
 * - 无限滚动加载
 * - 点击查看详情
 * - 删除记录
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { useAuthStore } from '../stores/authStore';
import type { HistoryItem, HistoryDetailResponse } from '../types';
import { ImageDetailModal } from '../components';

export function HistoryPage() {
  const navigate = useNavigate();
  const { user, clearAuth, refreshToken } = useAuthStore();
  
  // 历史记录状态
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);
  
  // 详情模态框状态
  const [selectedItem, setSelectedItem] = useState<HistoryDetailResponse | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  
  // 删除确认状态
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // 无限滚动观察器
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  const PAGE_SIZE = 20;

  /**
   * 加载历史记录
   */
  const loadHistory = useCallback(async (pageNum: number, append: boolean = false) => {
    if (pageNum === 1) {
      setIsLoading(true);
    } else {
      setIsLoadingMore(true);
    }
    setError(null);

    try {
      const response = await apiService.getHistory(pageNum, PAGE_SIZE);
      
      if (append) {
        setItems(prev => [...prev, ...response.items]);
      } else {
        setItems(response.items);
      }
      
      setTotal(response.total);
      setHasMore(response.has_more);
      setPage(pageNum);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '加载历史记录失败';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, []);

  /**
   * 初始加载
   */
  useEffect(() => {
    loadHistory(1);
  }, [loadHistory]);

  /**
   * 设置无限滚动观察器
   */
  useEffect(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoadingMore && !isLoading) {
          loadHistory(page + 1, true);
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [hasMore, isLoadingMore, isLoading, page, loadHistory]);

  /**
   * 查看详情
   */
  const handleViewDetail = async (item: HistoryItem) => {
    setIsLoadingDetail(true);
    setIsModalOpen(true);
    
    try {
      const detail = await apiService.getHistoryDetail(item.id);
      setSelectedItem(detail);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '加载详情失败';
      setError(errorMessage);
      setIsModalOpen(false);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  /**
   * 关闭详情模态框
   */
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedItem(null);
  };

  /**
   * 删除记录
   */
  const handleDelete = async (id: string) => {
    setIsDeleting(true);
    
    try {
      await apiService.deleteHistory(id);
      // 从列表中移除
      setItems(prev => prev.filter(item => item.id !== id));
      setTotal(prev => prev - 1);
      setDeleteConfirmId(null);
      
      // 如果删除的是当前查看的记录，关闭模态框
      if (selectedItem?.id === id) {
        handleCloseModal();
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '删除失败';
      setError(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };

  /**
   * 登出
   */
  const handleLogout = async () => {
    try {
      if (refreshToken) {
        await apiService.logout(refreshToken);
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      clearAuth();
      navigate('/login');
    }
  };

  /**
   * 格式化日期
   */
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  /**
   * 获取类型标签
   */
  const getTypeLabel = (type: string) => {
    return type === 'poster' ? '海报生成' : '场景融合';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      {/* 顶部导航栏 */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-900/95 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* 左侧：返回和标题 */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="p-2 text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-xl font-semibold text-white">生成历史</h1>
              {total > 0 && (
                <span className="text-sm text-gray-400">共 {total} 条记录</span>
              )}
            </div>

            {/* 右侧：用户信息 */}
            {user && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-300">
                  {user.phone || user.email}
                </span>
                <button
                  onClick={() => navigate('/subscription')}
                  className={`text-xs px-2 py-0.5 rounded-full cursor-pointer hover:opacity-80 transition-opacity ${
                    user.membership_tier === 'professional' 
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                      : user.membership_tier === 'basic'
                      ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      : 'bg-gray-500/20 text-gray-300 border border-gray-500/30'
                  }`}
                  title="会员订阅"
                >
                  {user.membership_tier === 'professional' ? '专业版' : user.membership_tier === 'basic' ? '基础版' : '免费版'}
                </button>
                <button
                  onClick={() => navigate('/subscription')}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                  title="会员订阅"
                >
                  👑
                </button>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                  title="退出登录"
                >
                  退出
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="pt-20 pb-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* 错误提示 */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-4 text-red-300 hover:text-red-200"
            >
              关闭
            </button>
          </div>
        )}

        {/* 加载状态 */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-4">
              <div className="animate-spin rounded-full h-12 w-12 border-2 border-indigo-500/30 border-t-indigo-500" />
              <span className="text-gray-400">加载中...</span>
            </div>
          </div>
        )}

        {/* 空状态 */}
        {!isLoading && items.length === 0 && (
          <EmptyState onNavigate={() => navigate('/')} />
        )}

        {/* 历史记录网格 */}
        {!isLoading && items.length > 0 && (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {items.map((item) => (
                <HistoryCard
                  key={item.id}
                  item={item}
                  onView={() => handleViewDetail(item)}
                  onDelete={() => setDeleteConfirmId(item.id)}
                  formatDate={formatDate}
                  getTypeLabel={getTypeLabel}
                />
              ))}
            </div>

            {/* 加载更多触发器 */}
            <div ref={loadMoreRef} className="py-8 flex justify-center">
              {isLoadingMore && (
                <div className="flex items-center gap-2 text-gray-400">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-indigo-500/30 border-t-indigo-500" />
                  <span>加载更多...</span>
                </div>
              )}
              {!hasMore && items.length > 0 && (
                <span className="text-gray-500">已加载全部记录</span>
              )}
            </div>
          </>
        )}
      </main>

      {/* 详情模态框 */}
      <ImageDetailModal
        isOpen={isModalOpen}
        isLoading={isLoadingDetail}
        item={selectedItem}
        onClose={handleCloseModal}
        onDelete={(id: string) => setDeleteConfirmId(id)}
        formatDate={formatDate}
        getTypeLabel={getTypeLabel}
      />

      {/* 删除确认对话框 */}
      {deleteConfirmId && (
        <DeleteConfirmDialog
          isDeleting={isDeleting}
          onConfirm={() => handleDelete(deleteConfirmId)}
          onCancel={() => setDeleteConfirmId(null)}
        />
      )}
    </div>
  );
}

/**
 * 历史记录卡片组件
 */
interface HistoryCardProps {
  item: HistoryItem;
  onView: () => void;
  onDelete: () => void;
  formatDate: (date: string) => string;
  getTypeLabel: (type: string) => string;
}

function HistoryCard({ item, onView, onDelete, formatDate, getTypeLabel }: HistoryCardProps) {
  return (
    <div className="group relative bg-gray-800/50 rounded-lg overflow-hidden border border-gray-700 hover:border-indigo-500/50 transition-all">
      {/* 缩略图 */}
      <div 
        className="aspect-square cursor-pointer"
        onClick={onView}
      >
        {item.thumbnail_url ? (
          <img
            src={item.thumbnail_url}
            alt="生成图片"
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-700">
            <svg className="w-12 h-12 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}
      </div>

      {/* 悬浮操作层 */}
      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
        <button
          onClick={onView}
          className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
          title="查看详情"
        >
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-2 bg-red-500/20 rounded-full hover:bg-red-500/40 transition-colors"
          title="删除"
        >
          <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>

      {/* 底部信息 */}
      <div className="p-2">
        <div className="flex items-center justify-between">
          <span className={`text-xs px-1.5 py-0.5 rounded ${
            item.type === 'poster' 
              ? 'bg-indigo-500/20 text-indigo-300' 
              : 'bg-emerald-500/20 text-emerald-300'
          }`}>
            {getTypeLabel(item.type)}
          </span>
          {item.has_watermark && (
            <span className="text-xs text-gray-500">水印</span>
          )}
        </div>
        <p className="mt-1 text-xs text-gray-400 truncate">
          {formatDate(item.created_at)}
        </p>
      </div>
    </div>
  );
}

/**
 * 空状态组件
 */
interface EmptyStateProps {
  onNavigate: () => void;
}

function EmptyState({ onNavigate }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-24 h-24 mb-6 rounded-full bg-gray-800 flex items-center justify-center">
        <svg className="w-12 h-12 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <h3 className="text-xl font-medium text-white mb-2">暂无生成记录</h3>
      <p className="text-gray-400 mb-6 text-center max-w-md">
        您还没有生成过任何图片。开始创作您的第一张海报或场景融合图片吧！
      </p>
      <button
        onClick={onNavigate}
        className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
      >
        开始创作
      </button>
    </div>
  );
}

/**
 * 删除确认对话框
 */
interface DeleteConfirmDialogProps {
  isDeleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function DeleteConfirmDialog({ isDeleting, onConfirm, onCancel }: DeleteConfirmDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-gray-800 rounded-lg p-6 max-w-sm w-full mx-4 border border-gray-700">
        <h3 className="text-lg font-medium text-white mb-2">确认删除</h3>
        <p className="text-gray-400 mb-6">
          删除后将无法恢复，确定要删除这条记录吗？
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={isDeleting}
            className="px-4 py-2 text-gray-300 hover:text-white transition-colors disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {isDeleting && (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" />
            )}
            {isDeleting ? '删除中...' : '确认删除'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default HistoryPage;
