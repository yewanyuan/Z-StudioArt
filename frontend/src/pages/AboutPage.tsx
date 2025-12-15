/**
 * About Page Component
 * Based on Mathilda Art Gallery Template - About Page Style
 * 关于我们页面 - 展示平台介绍、功能特色、技术能力
 */

import { Header, Footer } from '../components/layout';
import { useLanguageStore } from '../stores/languageStore';

// Translations
const ABOUT_TRANSLATIONS = {
  zh: {
    aboutUs: '关于我们',
    studioName: 'PopGraph Studio',
    studioDesc: 'AI 创意工作室',
    aboutText1: 'PopGraph Studio 是一个基于人工智能的创意设计平台，致力于帮助用户快速生成专业级的营销素材。我们利用最先进的 AIGC 技术，让每个人都能轻松创作出精美的海报和视觉内容。',
    aboutText2: '无论您是电商运营、品牌营销还是社交媒体推广，PopGraph Studio 都能满足您的创作需求。只需简单的文字描述，AI 即可为您生成独特而专业的视觉作品。',
    aboutText3: '我们相信，AI 技术应该让创意变得更加简单和高效。让我们一起，用 AI 释放无限创意！',
    platformAdvantages: '平台优势',
    technicalCapabilities: '技术能力',
    techDesc: '我们的平台基于多项先进的 AI 技术构建，为您提供专业级的图像生成和处理能力。',
    features: '功能特色',
    registeredUsers: '注册用户',
    generatedWorks: '生成作品',
    satisfaction: '满意度',
    onlineService: '在线服务',
    experiences: [
      { title: '高效创作', description: '基于最新的 AIGC 技术，几秒钟内即可生成专业级的营销海报，大幅提升创作效率。' },
      { title: '智能理解', description: '深度理解场景描述和营销文案，自动生成符合需求的视觉内容，无需专业设计技能。' },
      { title: '持续优化', description: '我们不断优化算法和模型，为用户提供更好的生成效果和更丰富的功能。' },
    ],
    skills: [
      { name: 'AI 图像生成', progress: 95 },
      { name: '场景融合', progress: 90 },
      { name: '文字排版', progress: 85 },
      { name: '智能构图', progress: 88 },
    ],
    featureList: [
      { icon: '🎨', title: '智能海报生成', description: '输入场景描述和营销文案，AI 自动生成图文并茂的商业海报，支持多种尺寸和风格模板。' },
      { icon: '🖼️', title: '场景融合', description: '上传白底商品图，AI 自动将其融合进指定的背景场景中，让商品展示更加生动。' },
      { icon: '📐', title: '灵活尺寸', description: '支持主流社交媒体尺寸 (1:1, 9:16, 16:9) 及自定义尺寸，满足不同平台发布需求。' },
      { icon: '📝', title: '智能模版', description: '内置多种营销模版，一键套用风格，快速创作专业级的营销素材。' },
    ],
  },
  en: {
    aboutUs: 'About Us',
    studioName: 'PopGraph Studio',
    studioDesc: 'AI Creative Studio',
    aboutText1: 'PopGraph Studio is an AI-powered creative design platform dedicated to helping users quickly generate professional marketing materials. We leverage cutting-edge AIGC technology to enable everyone to easily create beautiful posters and visual content.',
    aboutText2: 'Whether you are in e-commerce operations, brand marketing, or social media promotion, PopGraph Studio can meet your creative needs. With just a simple text description, AI can generate unique and professional visual works for you.',
    aboutText3: 'We believe AI technology should make creativity simpler and more efficient. Let\'s unleash unlimited creativity with AI together!',
    platformAdvantages: 'Platform Advantages',
    technicalCapabilities: 'Technical Capabilities',
    techDesc: 'Our platform is built on multiple advanced AI technologies to provide you with professional-grade image generation and processing capabilities.',
    features: 'Features',
    registeredUsers: 'Registered Users',
    generatedWorks: 'Generated Works',
    satisfaction: 'Satisfaction',
    onlineService: 'Online Service',
    experiences: [
      { title: 'Efficient Creation', description: 'Based on the latest AIGC technology, professional marketing posters can be generated in seconds, greatly improving creative efficiency.' },
      { title: 'Intelligent Understanding', description: 'Deep understanding of scene descriptions and marketing copy, automatically generating visual content that meets requirements without professional design skills.' },
      { title: 'Continuous Optimization', description: 'We continuously optimize algorithms and models to provide users with better generation results and richer features.' },
    ],
    skills: [
      { name: 'AI Image Generation', progress: 95 },
      { name: 'Scene Fusion', progress: 90 },
      { name: 'Text Layout', progress: 85 },
      { name: 'Smart Composition', progress: 88 },
    ],
    featureList: [
      { icon: '🎨', title: 'Smart Poster Generation', description: 'Input scene description and marketing copy, AI automatically generates illustrated commercial posters with multiple sizes and style templates.' },
      { icon: '🖼️', title: 'Scene Fusion', description: 'Upload product images with white background, AI automatically fuses them into specified background scenes for more vivid product display.' },
      { icon: '📐', title: 'Flexible Sizes', description: 'Support mainstream social media sizes (1:1, 9:16, 16:9) and custom sizes to meet different platform publishing needs.' },
      { icon: '📝', title: 'Smart Templates', description: 'Built-in various marketing templates, one-click style application for quick creation of professional marketing materials.' },
    ],
  },
};

export function AboutPage() {
  const { language } = useLanguageStore();
  const t = ABOUT_TRANSLATIONS[language];

  return (
    <div className="page-wrapper">
      {/* Background Curve */}
      <div className="bg-curve" />

      {/* Header */}
      <Header />

      {/* About Section */}
      <section className="about__page">
        <div className="container-main">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
            {/* About Us Column */}
            <div className="about__text">
              <h3 className="about__title">{t.aboutUs}</h3>
              <div className="about__meta">
                <img src="/img/logo.png" alt="PopGraph Studio" className="!w-20 !h-20 object-contain !rounded-lg" />
                <div className="about__meta__info">
                  <h5>{t.studioName}</h5>
                  <p>{t.studioDesc}</p>
                </div>
              </div>
              <p className="mb-4">{t.aboutText1}</p>
              <p className="mb-4">{t.aboutText2}</p>
              <p>{t.aboutText3}</p>
            </div>

            {/* Experience Column */}
            <div className="experience__text">
              <h3 className="about__title">{t.platformAdvantages}</h3>
              {t.experiences.map((item, index) => (
                <div key={index} className="experience__item">
                  <h4>{item.title}</h4>
                  <p>{item.description}</p>
                </div>
              ))}
            </div>

            {/* Skills Column */}
            <div className="skills__text">
              <h3 className="about__title">{t.technicalCapabilities}</h3>
              <p>{t.techDesc}</p>
              {t.skills.map((skill, index) => (
                <div key={index} className="single-progress-item">
                  <h6>{skill.name}</h6>
                  <div className="progress-bar-wrapper">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${skill.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 lg:py-20 bg-[var(--primary-bg)]">
        <div className="container-main">
          <div className="text-center mb-12">
            <h2 className="section-title">{t.features}</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {t.featureList.map((feature, index) => (
              <div
                key={index}
                className="card p-6 text-center hover:shadow-xl transition-shadow duration-300"
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h4 className="text-[var(--text-dark)] mb-3">{feature.title}</h4>
                <p className="text-sm text-[var(--text-muted)]">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-[var(--bg-light)]">
        <div className="container-main">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl lg:text-5xl font-bold text-[var(--primary)] mb-2">10K+</div>
              <p className="text-[var(--text-muted)]">{t.registeredUsers}</p>
            </div>
            <div>
              <div className="text-4xl lg:text-5xl font-bold text-[var(--primary)] mb-2">50K+</div>
              <p className="text-[var(--text-muted)]">{t.generatedWorks}</p>
            </div>
            <div>
              <div className="text-4xl lg:text-5xl font-bold text-[var(--primary)] mb-2">99%</div>
              <p className="text-[var(--text-muted)]">{t.satisfaction}</p>
            </div>
            <div>
              <div className="text-4xl lg:text-5xl font-bold text-[var(--primary)] mb-2">24/7</div>
              <p className="text-[var(--text-muted)]">{t.onlineService}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
}

export default AboutPage;
