/**
 * 作品展示页面 (Gallery)
 * Based on Mathilda Art Gallery Template - Gallery Style
 * Requirements: 9.1, 9.2
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiService } from '../services/api';
import { useAuthStore } from '../stores/authStore';
import { useLanguageStore } from '../stores/languageStore';
import type { HistoryItem, HistoryDetailResponse } from '../types';
import { ImageDetailModal } from '../components';
import { Header, Footer } from '../components/layout';

// Translations
const GALLERY_TRANSLATIONS = {
  zh: {
    pageTitle: '作品展示',
    totalRecords: '共 {count} 条创作记录',
    loginToView: '登录后查看您的创作历史',
    filterAll: '全部',
    filterPoster: '海报',
    filterScene: '场景',
    loginTitle: '登录查看您的作品',
    loginDesc: '登录后即可查看您的所有创作历史记录',
    loginNow: '立即登录',
    loading: '加载中...',
    loadingMore: '加载更多...',
    allLoaded: '已加载全部记录',
    emptyTitle: '暂无创作记录',
    emptyDesc: '您还没有生成过任何图片。开始创作您的第一张海报或场景融合图片吧！',
    startCreating: '开始创作',
    view: '查看',
    delete: '删除',
    watermark: '水印',
    typeLabels: { poster: '海报生成', scene: '场景融合' },
    deleteConfirmTitle: '确认删除',
    deleteConfirmDesc: '删除后将无法恢复，确定要删除这条记录吗？',
    cancel: '取消',
    confirmDelete: '确认删除',
    deleting: '删除中...',
  },
  en: {
    pageTitle: 'Gallery',
    totalRecords: '{count} creation records',
    loginToView: 'Log in to view your creation history',
    filterAll: 'All',
    filterPoster: 'Poster',
    filterScene: 'Scene',
    loginTitle: 'Log in to view your works',
    loginDesc: 'Log in to view all your creation history',
    loginNow: 'Log In',
    loading: 'Loading...',
    loadingMore: 'Loading more...',
    allLoaded: 'All records loaded',
    emptyTitle: 'No creation records',
    emptyDesc: 'You haven\'t generated any images yet. Start creating your first poster or scene fusion image!',
    startCreating: 'Start Creating',
    view: 'View',
    delete: 'Delete',
    watermark: 'Watermark',
    typeLabels: { poster: 'Poster', scene: 'Scene Fusion' },
    deleteConfirmTitle: 'Confirm Delete',
    deleteConfirmDesc: 'This action cannot be undone. Are you sure you want to delete this record?',
    cancel: 'Cancel',
    confirmDelete: 'Confirm Delete',
    deleting: 'Deleting...',
  },
};

export function HistoryPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { language } = useLanguageStore();
  const t = GALLERY_TRANSLATIONS[language];

  const [items, setItems] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);

  const [selectedItem, setSelectedItem] = useState<HistoryDetailResponse | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [filterType, setFilterType] = useState<'all' | 'poster' | 'scene'>('all');

  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  const PAGE_SIZE = 20;

  const loadHistory = useCallback(async (pageNum: number, append: boolean = false) => {
    if (!isAuthenticated) return;

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
      const errorMessage = err instanceof Error ? err.message : (language === 'zh' ? '加载历史记录失败' : 'Failed to load history');
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, [isAuthenticated, language]);

  useEffect(() => {
    if (isAuthenticated) {
      loadHistory(1);
    }
  }, [loadHistory, isAuthenticated]);

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

  const handleViewDetail = async (item: HistoryItem) => {
    setIsLoadingDetail(true);
    setIsModalOpen(true);

    try {
      const detail = await apiService.getHistoryDetail(item.id);
      setSelectedItem(detail);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : (language === 'zh' ? '加载详情失败' : 'Failed to load details');
      setError(errorMessage);
      setIsModalOpen(false);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedItem(null);
  };

  const handleDelete = async (id: string) => {
    setIsDeleting(true);

    try {
      await apiService.deleteHistory(id);
      setItems(prev => prev.filter(item => item.id !== id));
      setTotal(prev => prev - 1);
      setDeleteConfirmId(null);

      if (selectedItem?.id === id) {
        handleCloseModal();
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : (language === 'zh' ? '删除失败' : 'Failed to delete');
      setError(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString(language === 'zh' ? 'zh-CN' : 'en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTypeLabel = (type: string) => {
    return type === 'poster' ? t.typeLabels.poster : t.typeLabels.scene;
  };

  const filteredItems = filterType === 'all'
    ? items
    : items.filter(item => item.type === filterType);

  return (
    <div className="page-wrapper">
      <div className="bg-curve" />
      <Header />

      <section className="py-8 border-b border-[var(--border-light)]">
        <div className="container-main">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h2 className="section-title mb-0">{t.pageTitle}</h2>
              <p className="text-[var(--text-muted)] mt-2">
                {isAuthenticated ? t.totalRecords.replace('{count}', String(total)) : t.loginToView}
              </p>
            </div>

            {isAuthenticated && items.length > 0 && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setFilterType('all')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    filterType === 'all'
                      ? 'bg-[var(--primary)] text-white'
                      : 'bg-[var(--primary-bg)] text-[var(--text-muted)] hover:text-[var(--primary)]'
                  }`}
                >
                  {t.filterAll}
                </button>
                <button
                  onClick={() => setFilterType('poster')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    filterType === 'poster'
                      ? 'bg-[var(--primary)] text-white'
                      : 'bg-[var(--primary-bg)] text-[var(--text-muted)] hover:text-[var(--primary)]'
                  }`}
                >
                  {t.filterPoster}
                </button>
                <button
                  onClick={() => setFilterType('scene')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    filterType === 'scene'
                      ? 'bg-[var(--primary)] text-white'
                      : 'bg-[var(--primary-bg)] text-[var(--text-muted)] hover:text-[var(--primary)]'
                  }`}
                >
                  {t.filterScene}
                </button>
              </div>
            )}
          </div>
        </div>
      </section>

      <main className="main-content">
        <div className="container-main">
          {!isAuthenticated && (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="w-24 h-24 mb-6 rounded-full bg-[var(--primary-bg)] flex items-center justify-center">
                <svg className="w-12 h-12 text-[var(--primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-medium text-[var(--text-dark)] mb-2">{t.loginTitle}</h3>
              <p className="text-[var(--text-muted)] mb-6 text-center max-w-md">{t.loginDesc}</p>
              <Link to="/login" className="btn-primary">{t.loginNow}</Link>
            </div>
          )}

          {error && (
            <div className="alert alert-error flex items-start gap-3 mb-6">
              <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-sm flex-1">{error}</p>
              <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}

          {isAuthenticated && isLoading && (
            <div className="flex items-center justify-center py-20">
              <div className="flex flex-col items-center gap-4">
                <div className="loader-spinner" />
                <span className="text-[var(--text-muted)]">{t.loading}</span>
              </div>
            </div>
          )}

          {isAuthenticated && !isLoading && items.length === 0 && (
            <EmptyState onNavigate={() => navigate('/create')} t={t} />
          )}

          {isAuthenticated && !isLoading && filteredItems.length > 0 && (
            <>
              <div className="gallery-grid">
                {filteredItems.map((item) => (
                  <GalleryCard
                    key={item.id}
                    item={item}
                    onView={() => handleViewDetail(item)}
                    onDelete={() => setDeleteConfirmId(item.id)}
                    formatDate={formatDate}
                    getTypeLabel={getTypeLabel}
                    t={t}
                    language={language}
                  />
                ))}
              </div>

              <div ref={loadMoreRef} className="py-8 flex justify-center">
                {isLoadingMore && (
                  <div className="flex items-center gap-2 text-[var(--text-muted)]">
                    <div className="loader-spinner w-5 h-5" />
                    <span>{t.loadingMore}</span>
                  </div>
                )}
                {!hasMore && items.length > 0 && (
                  <span className="text-[var(--text-muted)]">{t.allLoaded}</span>
                )}
              </div>
            </>
          )}
        </div>
      </main>

      <Footer />

      <ImageDetailModal
        isOpen={isModalOpen}
        isLoading={isLoadingDetail}
        item={selectedItem}
        onClose={handleCloseModal}
        onDelete={(id: string) => setDeleteConfirmId(id)}
        formatDate={formatDate}
        getTypeLabel={getTypeLabel}
      />

      {deleteConfirmId && (
        <DeleteConfirmDialog
          isDeleting={isDeleting}
          onConfirm={() => handleDelete(deleteConfirmId)}
          onCancel={() => setDeleteConfirmId(null)}
          t={t}
        />
      )}
    </div>
  );
}

interface GalleryCardProps {
  item: HistoryItem;
  onView: () => void;
  onDelete: () => void;
  formatDate: (date: string) => string;
  getTypeLabel: (type: string) => string;
  t: typeof GALLERY_TRANSLATIONS.zh;
  language: 'zh' | 'en';
}

function GalleryCard({ item, onView, onDelete, formatDate, getTypeLabel, t, language }: GalleryCardProps) {
  return (
    <div className="gallery-item group">
      <div className="aspect-square cursor-pointer overflow-hidden" onClick={onView}>
        {item.thumbnail_url ? (
          <img
            src={item.thumbnail_url}
            alt={language === 'zh' ? '生成图片' : 'Generated image'}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-[var(--primary-bg)]">
            <svg className="w-12 h-12 text-[var(--primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}
      </div>

      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
        <span className={`self-start text-xs px-2 py-1 rounded mb-2 ${
          item.type === 'poster' ? 'bg-[var(--primary)] text-white' : 'bg-emerald-500 text-white'
        }`}>
          {getTypeLabel(item.type)}
        </span>

        <p className="text-xs text-white/80">{formatDate(item.created_at)}</p>

        <div className="flex items-center gap-2 mt-3">
          <button
            onClick={onView}
            className="flex-1 py-2 bg-white/20 rounded-lg text-white text-sm font-medium hover:bg-white/30 transition-colors"
          >
            {t.view}
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="p-2 bg-red-500/20 rounded-lg hover:bg-red-500/40 transition-colors"
            title={t.delete}
          >
            <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      {item.has_watermark && (
        <div className="absolute top-2 right-2 px-2 py-1 bg-black/50 rounded text-xs text-white/70">
          {t.watermark}
        </div>
      )}
    </div>
  );
}

interface EmptyStateProps {
  onNavigate: () => void;
  t: typeof GALLERY_TRANSLATIONS.zh;
}

function EmptyState({ onNavigate, t }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-24 h-24 mb-6 rounded-full bg-[var(--primary-bg)] flex items-center justify-center">
        <svg className="w-12 h-12 text-[var(--primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <h3 className="text-xl font-medium text-[var(--text-dark)] mb-2">{t.emptyTitle}</h3>
      <p className="text-[var(--text-muted)] mb-6 text-center max-w-md">{t.emptyDesc}</p>
      <button onClick={onNavigate} className="btn-primary">{t.startCreating}</button>
    </div>
  );
}

interface DeleteConfirmDialogProps {
  isDeleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  t: typeof GALLERY_TRANSLATIONS.zh;
}

function DeleteConfirmDialog({ isDeleting, onConfirm, onCancel, t }: DeleteConfirmDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="card max-w-sm w-full mx-4 animate-fadeIn">
        <div className="card-body">
          <h3 className="text-lg font-bold text-[var(--text-dark)] mb-2">{t.deleteConfirmTitle}</h3>
          <p className="text-[var(--text-muted)] mb-6">{t.deleteConfirmDesc}</p>
          <div className="flex gap-3 justify-end">
            <button onClick={onCancel} disabled={isDeleting} className="btn-secondary px-4 py-2 disabled:opacity-50">
              {t.cancel}
            </button>
            <button
              onClick={onConfirm}
              disabled={isDeleting}
              className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isDeleting && <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              {isDeleting ? t.deleting : t.confirmDelete}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HistoryPage;
