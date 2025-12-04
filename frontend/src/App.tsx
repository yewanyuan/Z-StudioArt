import { useState } from 'react';
import './App.css';
import { PosterGeneratorPage } from './components/PosterGeneratorPage';
import { SceneFusionPage } from './components/SceneFusionPage';

type PageType = 'poster' | 'scene-fusion';

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('poster');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      {/* Navigation */}
      <nav className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50">
        <div className="flex gap-2 p-2 bg-gray-800/90 backdrop-blur-sm rounded-full border border-gray-700 shadow-lg">
          <button
            onClick={() => setCurrentPage('poster')}
            className={`px-6 py-2 rounded-full text-sm font-medium transition-colors ${
              currentPage === 'poster'
                ? 'bg-red-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-700'
            }`}
          >
            🎨 海报生成
          </button>
          <button
            onClick={() => setCurrentPage('scene-fusion')}
            className={`px-6 py-2 rounded-full text-sm font-medium transition-colors ${
              currentPage === 'scene-fusion'
                ? 'bg-red-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-700'
            }`}
          >
            🖼️ 场景融合
          </button>
        </div>
      </nav>

      {/* Page Content */}
      {currentPage === 'poster' && <PosterGeneratorPage />}
      {currentPage === 'scene-fusion' && <SceneFusionPage />}
    </div>
  );
}

export default App;
