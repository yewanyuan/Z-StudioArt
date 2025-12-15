/**
 * 首页组件
 * Based on Mathilda Art Gallery Template - Hero Slider Style
 * 展示产品特色和最新作品
 */

import { useRef } from 'react';
import { Link } from 'react-router-dom';
import Slider from 'react-slick';
import { Header, Footer } from '../components/layout';
import { useLanguageStore } from '../stores/languageStore';

// Import slick carousel CSS
import 'slick-carousel/slick/slick.css';
import 'slick-carousel/slick/slick-theme.css';

// 示例展示图片
const SHOWCASE_IMAGES = [
  { id: 1, src: '/img/hero-slider/1.jpg', title: 'Natural', category: 'Painting' },
  { id: 2, src: '/img/hero-slider/2.jpg', title: 'Painting Brush', category: 'Painting' },
  { id: 3, src: '/img/hero-slider/3.jpg', title: 'Blue Sky', category: 'Painting' },
  { id: 4, src: '/img/hero-slider/4.jpg', title: 'Wall Art', category: 'Painting' },
  { id: 5, src: '/img/hero-slider/5.jpg', title: 'Colour Hand', category: 'Painting' },
  { id: 6, src: '/img/hero-slider/6.jpg', title: 'Darkness with Beauty', category: 'Painting' },
  { id: 7, src: '/img/hero-slider/7.jpg', title: 'Maze', category: 'Painting' },
];

// Translations
const HOME_TRANSLATIONS = {
  zh: {
    ctaTitle: '海报创作工坊',
    ctaSubtitle1: '智能设计，触手可及',
    ctaSubtitle2: '赋予文字以视觉生命，利用先进 AIGC 技术，让品牌故事更加生动有力',
    startCreating: '开始创作',
    learnMore: '了解更多',
  },
  en: {
    ctaTitle: 'Poster Creation Workshop',
    ctaSubtitle1: 'Intelligent Design, Within Reach',
    ctaSubtitle2: 'Give visual life to words, use advanced AIGC technology to make brand stories more vivid and powerful',
    startCreating: 'Start Creating',
    learnMore: 'Learn More',
  },
};

export function HomePage() {
  const heroSliderRef = useRef<Slider>(null);
  const textSliderRef = useRef<Slider>(null);
  const { language } = useLanguageStore();
  const t = HOME_TRANSLATIONS[language];

  // Hero slider settings - matches template's main.js configuration
  const heroSliderSettings = {
    dots: false,
    infinite: true,
    speed: 400,
    slidesToShow: 1,
    centerMode: true,
    variableWidth: true,
    arrows: false,
    autoplay: true,
    pauseOnHover: false,
    autoplaySpeed: 3000,
    asNavFor: textSliderRef.current || undefined,
    beforeChange: (_current: number, next: number) => {
      textSliderRef.current?.slickGoTo(next);
    },
    responsive: [
      {
        breakpoint: 480,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1,
        },
      },
    ],
  };

  // Text slider settings
  const textSliderSettings = {
    dots: false,
    infinite: false,
    speed: 400,
    arrows: false,
    fade: true,
    asNavFor: heroSliderRef.current || undefined,
  };

  // Handle wheel event for slider navigation
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (e.deltaY > 0) {
      heroSliderRef.current?.slickNext();
    } else {
      heroSliderRef.current?.slickPrev();
    }
  };

  // Handle slide click to navigate
  const handleSlideClick = (index: number) => {
    heroSliderRef.current?.slickGoTo(index);
  };

  return (
    <div className="page-wrapper">
      {/* Background Curve - positioned absolute to page wrapper */}
      <div className="bg-curve" />

      {/* Header */}
      <Header />

      {/* Hero Section - Slider */}
      <section className="hero__section">
        {/* Hero Slider */}
        <div className="hero-slider-wrapper" onWheel={handleWheel}>
          <Slider ref={heroSliderRef} {...heroSliderSettings} className="hero-slider">
            {SHOWCASE_IMAGES.map((image, index) => (
              <div key={image.id} className="slide-item" onClick={() => handleSlideClick(index)}>
                <img
                  src={image.src}
                  alt={image.title}
                  draggable={false}
                />
              </div>
            ))}
          </Slider>
        </div>

        {/* Hero Text Slider */}
        <div className="hero-text-slider">
          <Slider ref={textSliderRef} {...textSliderSettings}>
            {SHOWCASE_IMAGES.map((image) => (
              <div key={image.id} className="text-item">
                <h2>{image.title}</h2>
                <p>{image.category}</p>
              </div>
            ))}
          </Slider>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container-main">
          <div className="cta-card">
            <h2 className="cta-title">{t.ctaTitle}</h2>
            <p className="cta-subtitle-line1">{t.ctaSubtitle1}</p>
            <p className="cta-subtitle-line2">{t.ctaSubtitle2}</p>
            <div className="cta-buttons">
              <Link to="/create" className="cta-btn-primary">
                {t.startCreating}
              </Link>
              <Link to="/about" className="cta-btn-secondary">
                {t.learnMore}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
}

export default HomePage;
