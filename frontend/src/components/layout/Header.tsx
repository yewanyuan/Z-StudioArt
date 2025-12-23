/**
 * Header Component
 * Based on Mathilda Art Gallery Template
 * Includes logo, navigation, language switch, and user actions
 */

import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useLanguageStore } from '../../stores/languageStore';
import { apiService } from '../../services/api';

interface NavItem {
  path: string;
  label: string;
  labelZh: string;
}

const NAV_ITEMS: NavItem[] = [
  { path: '/', label: 'Home', labelZh: '首页' },
  { path: '/about', label: 'About', labelZh: '关于' },
  { path: '/create', label: 'Create', labelZh: '创作' },
  { path: '/gallery', label: 'Gallery', labelZh: '作品' },
  { path: '/subscription', label: 'Plans', labelZh: '订阅' },
];

export function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, clearAuth, refreshToken } = useAuthStore();
  const { language, setLanguage } = useLanguageStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <header className="header">
      <div className="container-fluid px-4 lg:px-12">
        <div className="relative flex items-center justify-between py-6">
          {/* Social Links - Left (desktop only) */}
          <div className="hidden sm:flex items-center gap-1 w-[200px]">
            <a href="#" className="btn-social">
              <i className="fa-brands fa-facebook-f"></i>
            </a>
            <a href="#" className="btn-social">
              <i className="fa-brands fa-twitter"></i>
            </a>
            <a href="#" className="btn-social">
              <i className="fa-brands fa-pinterest"></i>
            </a>
            <a href="#" className="btn-social">
              <i className="fa-brands fa-instagram"></i>
            </a>
          </div>

          {/* Language Switch - Left on mobile only */}
          <div className="block sm:hidden">
            <div className="language-switch">
              <button
                type="button"
                onClick={() => setLanguage('zh')}
                className={`lang-btn ${language === 'zh' ? 'active' : ''}`}
                aria-pressed={language === 'zh'}
              >
                中文
              </button>
              <button
                type="button"
                onClick={() => setLanguage('en')}
                className={`lang-btn ${language === 'en' ? 'active' : ''}`}
                aria-pressed={language === 'en'}
              >
                EN
              </button>
            </div>
          </div>

          {/* Logo - Center (absolute positioning for true center) */}
          <div className="absolute left-1/2 transform -translate-x-1/2">
            <Link to="/" className="inline-block">
              <img src="/img/logo.png" alt="PopGraph Studio" className="h-12 md:h-16" />
            </Link>
          </div>

          {/* Right Actions - Language Switch & User */}
          <div className="flex items-center gap-3 ml-auto">
            {/* Language Switch - desktop only */}
            <div className="hidden sm:block">
              <div className="language-switch">
                <button
                  type="button"
                  onClick={() => setLanguage('zh')}
                  className={`lang-btn ${language === 'zh' ? 'active' : ''}`}
                  aria-pressed={language === 'zh'}
                >
                  中文
                </button>
                <button
                  type="button"
                  onClick={() => setLanguage('en')}
                  className={`lang-btn ${language === 'en' ? 'active' : ''}`}
                  aria-pressed={language === 'en'}
                >
                  EN
                </button>
              </div>
            </div>

            {isAuthenticated ? (
              <>
                {/* User Info */}
                <div className="hidden md:flex items-center gap-3">
                  <span className="text-sm text-[var(--text-muted)]">
                    {user?.email?.split('@')[0] || user?.phone}
                  </span>
                  <span className="px-2 py-1 text-xs font-semibold text-white bg-[var(--primary)] rounded">
                    {user?.membership_tier === 'professional' ? 'PRO' : user?.membership_tier === 'basic' ? 'BASIC' : 'FREE'}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="btn-social"
                  title="退出登录"
                >
                  <i className="fa fa-sign-out"></i>
                </button>
              </>
            ) : (
              <Link to="/login" className="btn-social" title="登录">
                <i className="fa fa-user"></i>
              </Link>
            )}

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="btn-social sm:hidden"
            >
              <i className="fa fa-bars"></i>
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="main__menu">
          {/* Desktop Navigation */}
          <ul className="nav__menu hidden sm:flex justify-center gap-8 pb-4">
            {NAV_ITEMS.map((item) => (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`nav-link relative text-base font-bold uppercase tracking-wide transition-colors ${
                    isActive(item.path)
                      ? 'text-[var(--primary)] menu--active'
                      : 'text-[var(--text-light)] hover:text-[var(--primary)]'
                  }`}
                >
                  {language === 'zh' ? item.labelZh : item.label}
                  {isActive(item.path) && (
                    <span className="absolute left-0 bottom-0 w-full h-1.5 bg-[var(--primary)] -z-10 transform skew-x-[70deg]" />
                  )}
                </Link>
              </li>
            ))}
          </ul>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="sm:hidden bg-white border-t border-[var(--border-light)] py-4">
              <ul className="flex flex-col gap-2">
                {NAV_ITEMS.map((item) => (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`block px-4 py-3 text-base font-bold transition-colors ${
                        isActive(item.path)
                          ? 'text-[var(--primary)] bg-[var(--primary-bg)]'
                          : 'text-[var(--text-dark)] hover:bg-[var(--primary-bg)]'
                      }`}
                    >
                      {language === 'zh' ? item.labelZh : item.label}
                    </Link>
                  </li>
                ))}
                {isAuthenticated && (
                  <li>
                    <button
                      onClick={() => {
                        setMobileMenuOpen(false);
                        handleLogout();
                      }}
                      className="block w-full text-left px-4 py-3 text-base font-bold text-red-500 hover:bg-red-50 transition-colors"
                    >
                      {language === 'zh' ? '退出登录' : 'Logout'}
                    </button>
                  </li>
                )}
              </ul>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;
