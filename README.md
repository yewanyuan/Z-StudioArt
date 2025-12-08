# PopGraph Studio (Z-StudioArt) 🎨

**PopGraph Studio** 是一款基于 AI 的智能设计工具，专注于为电商和营销场景生成高质量的**爆款海报**与**产品场景图**。

它结合了最新的 AIGC 技术（Z-Image-Turbo）与现代化的 Web 交互体验，让用户能够通过简单的文字描述，在几秒钟内生成专业级的营销素材。

![Status](https://img.shields.io/badge/Status-Beta-blue) ![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ 核心功能 (Key Features)

*   **🎨 智能海报生成 (AI Poster Generation)**: 输入场景描述和营销文案，AI 自动生成图文并茂的商业海报。
*   **🛍️ 场景融合 (Scene Fusion)**: 上传白底商品图，AI 自动将其融合进指定的背景场景中（虚拟摄影棚）。
*   **📐 灵活尺寸支持 (Multi-Dimension)**: 支持主流社交媒体尺寸 (1:1, 9:16, 16:9) 及**自定义宽高** (Custom Size)。
*   **📝 智能模版 (Smart Templates)**: 内置多种营销模版（促销、节日、高级感），一键套用风格。
*   **🌍 双语支持 (Internationalization)**: 完美支持中文与英文界面切换，适应全球化创作需求。
*   **💎 现代 UI 设计 (Glassmorphism)**: 采用深色毛玻璃风格设计，提供沉浸式的创作体验。

## 🛠 技术栈 (Tech Stack)

### Frontend (前端)
*   **Framework**: React 18 + Vite
*   **Language**: TypeScript
*   **Styling**: Tailwind CSS (Glassmorphism Design System)
*   **HTTP Client**: Axios
*   **State**: React Hooks

### Backend (后端)
*   **Framework**: FastAPI (Python)
*   **AI Model**: ModelScope Z-Image-Turbo (via API)
*   **Database**: PostgreSQL + SQLAlchemy
*   **Cache**: Redis
*   **Image Processing**: Pillow (PIL) for watermarking & resizing
*   **Testing**: Pytest + Hypothesis (Property-Based Testing)
*   **Concurrency**: Python Asyncio

---

## 🚀 快速开始 (Getting Started)

### 1. 克隆项目
```bash
git clone https://github.com/xiongfazhan/Z-StudioArt.git
cd Z-StudioArt
```

### 2. 后端设置 (Backend)

确保你已安装 Python 3.10+。

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt  # 如果没有 requirements.txt，请手动安装: fastapi uvicorn httpx pillow python-dotenv pydantic

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 ModelScope API Key
```

**启动后端服务：**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端设置 (Frontend)

确保你已安装 Node.js 18+。

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量 (可选，默认为 localhost:8000)
cp .env.example .env

# 启动开发服务器
npm run dev
```

打开浏览器访问 `http://localhost:5173` 即可开始创作！

---

## ⚙️ 环境变量配置

### Backend (`backend/.env`)
| 变量名 | 描述 | 默认值/示例 |
|or|---|---|
| `MODELSCOPE_API_KEY` | **[必需]** 阿里 ModelScope API 密钥 | `ms-...` |
| `MODELSCOPE_BASE_URL`| ModelScope API 地址 | `https://api-inference.modelscope.cn/` |
| `ZIMAGE_TIMEOUT` | 生成超时时间 (ms) | `30000` |

### Frontend (`frontend/.env`)
| 变量名 | 描述 | 默认值 |
|---|---|---|
| `VITE_API_BASE_URL` | 后端 API 地址 | `http://localhost:8000` |

---

## 🖼️ 预览截图

*(此处可以添加项目的实际截图)*

---

## 🤝 贡献 (Contributing)

欢迎提交 Issue 或 Pull Request 来改进这个项目！

1.  Fork 本仓库
2.  新建 Feature 分支 (`git checkout -b feature/AmazingFeature`)
3.  提交更改 (`git commit -m 'Add some AmazingFeature'`)
4.  推送到分支 (`git push origin feature/AmazingFeature`)
5.  提交 Pull Request

## � D可ocker 部署

使用 Docker Compose 快速部署：

```bash
# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入必要配置

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

详细部署指南请参考 [DEPLOYMENT.md](./DEPLOYMENT.md)。

## 🧪 运行测试

### 后端测试
```bash
cd backend
pytest tests/ -v
```

### 前端测试
```bash
cd frontend
npm test
```

## 📄 许可证 (License)

Distributed under the MIT License. See `LICENSE` for more information.
