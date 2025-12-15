/**
 * Footer Component
 * Based on Mathilda Art Gallery Template
 */

import { Link } from 'react-router-dom';
import { useLanguageStore } from '../../stores/languageStore';

// Translations
const FOOTER_TRANSLATIONS = {
  zh: {
    brandLine1: 'AI 智能海报生成工具',
    brandLine2: '让创意触手可及',
    quickLinks: '快速链接',
    home: '首页',
    startCreating: '开始创作',
    gallery: '作品展示',
    subscription: '订阅计划',
    features: '功能特色',
    smartPoster: '智能海报生成',
    sceneFusion: '场景融合',
    multiSize: '多尺寸支持',
    templates: '模板系统',
    contactUs: '联系我们',
    email: '邮箱',
    phone: '电话',
  },
  en: {
    brandLine1: 'AI Smart Poster Generator',
    brandLine2: 'Creativity at your fingertips',
    quickLinks: 'Quick Links',
    home: 'Home',
    startCreating: 'Start Creating',
    gallery: 'Gallery',
    subscription: 'Subscription',
    features: 'Features',
    smartPoster: 'Smart Poster Generation',
    sceneFusion: 'Scene Fusion',
    multiSize: 'Multiple Sizes',
    templates: 'Template System',
    contactUs: 'Contact Us',
    email: 'Email',
    phone: 'Phone',
  },
};

export function Footer() {
  const currentYear = new Date().getFullYear();
  const { language } = useLanguageStore();
  const t = FOOTER_TRANSLATIONS[language];

  return (
    <footer className="footer__section py-8 border-t border-[var(--border-light)]">
      <div className="container-main">
        {/* Footer Links */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <Link to="/" className="inline-block mb-4">
              <img src="/img/logo.png" alt="PopGraph Studio" className="h-10" />
            </Link>
            <p className="text-sm text-[var(--text-muted)] leading-relaxed">
              {t.brandLine1}
            </p>
            <p className="text-sm text-[var(--text-muted)] leading-relaxed">
              {t.brandLine2}
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h6 className="text-[var(--text-dark)] font-bold mb-4">{t.quickLinks}</h6>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="text-sm text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors">
                  {t.home}
                </Link>
              </li>
              <li>
                <Link to="/create" className="text-sm text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors">
                  {t.startCreating}
                </Link>
              </li>
              <li>
                <Link to="/gallery" className="text-sm text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors">
                  {t.gallery}
                </Link>
              </li>
              <li>
                <Link to="/subscription" className="text-sm text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors">
                  {t.subscription}
                </Link>
              </li>
            </ul>
          </div>

          {/* Features */}
          <div>
            <h6 className="text-[var(--text-dark)] font-bold mb-4">{t.features}</h6>
            <ul className="space-y-2">
              <li className="text-sm text-[var(--text-muted)]">{t.smartPoster}</li>
              <li className="text-sm text-[var(--text-muted)]">{t.sceneFusion}</li>
              <li className="text-sm text-[var(--text-muted)]">{t.multiSize}</li>
              <li className="text-sm text-[var(--text-muted)]">{t.templates}</li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h6 className="text-[var(--text-dark)] font-bold mb-4">{t.contactUs}</h6>
            <ul className="space-y-2">
              <li className="text-sm text-[var(--text-muted)]">
                <span className="text-[var(--primary)] font-semibold">{t.email}：</span>
                support@popgraph.com
              </li>
              <li className="text-sm text-[var(--text-muted)]">
                <span className="text-[var(--primary)] font-semibold">{t.phone}：</span>
                400-888-8888
              </li>
            </ul>
            {/* Social Links */}
            <div className="flex gap-2 mt-4">
              <a href="#" className="btn-social text-sm">
                <i className="fa-brands fa-weixin"></i>
              </a>
              <a href="#" className="btn-social text-sm">
                <i className="fa-brands fa-weibo"></i>
              </a>
              <a href="#" className="btn-social text-sm">
                <i className="fa-brands fa-github"></i>
              </a>
            </div>
          </div>
        </div>

        {/* Copyright */}
        <div className="footer__copyright__text text-center pt-6 border-t border-[var(--border-light)]">
          <p className="text-sm text-[var(--text-muted)]">
            Copyright &copy; {currentYear} PopGraph Studio. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
