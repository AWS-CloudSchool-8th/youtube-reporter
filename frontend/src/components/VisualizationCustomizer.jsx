// frontend/src/components/VisualizationCustomizer.jsx
import React, { useState } from 'react';

const VisualizationCustomizer = ({ onThemeChange, onSizeChange, currentTheme, currentSize }) => {
  const [isOpen, setIsOpen] = useState(false);

  const themes = {
    website: {
      name: '웹사이트 테마',
      colors: ['#667eea', '#764ba2', '#ec4899', '#f093fb', '#6366f1', '#4f46e5'],
      description: '웹사이트와 어울리는 보라색 계열'
    },
    professional: {
      name: '프로페셔널',
      colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
      description: '비즈니스용 깔끔한 색상'
    },
    warm: {
      name: '따뜻한 색상',
      colors: ['#f59e0b', '#ef4444', '#f97316', '#eab308', '#dc2626', '#ea580c'],
      description: '따뜻하고 활기찬 느낌'
    },
    cool: {
      name: '차가운 색상',
      colors: ['#06b6d4', '#0891b2', '#3b82f6', '#1d4ed8', '#6366f1', '#4338ca'],
      description: '시원하고 차분한 느낌'
    },
    nature: {
      name: '자연 색상',
      colors: ['#10b981', '#059669', '#84cc16', '#65a30d', '#22c55e', '#16a34a'],
      description: '자연스럽고 편안한 색상'
    }
  };

  const sizes = {
    compact: { name: '컴팩트', height: 250, description: '작고 간결하게' },
    normal: { name: '보통', height: 300, description: '적당한 크기' },
    large: { name: '크게', height: 400, description: '큰 화면에서 보기' }
  };

  return (
    <div className="viz-customizer">
      <button 
        className="customizer-toggle"
        onClick={() => setIsOpen(!isOpen)}
      >
        🎨 스타일 설정
      </button>

      {isOpen && (
        <div className="customizer-panel">
          <div className="customizer-section">
            <h4>색상 테마</h4>
            <div className="theme-grid">
              {Object.entries(themes).map(([key, theme]) => (
                <div 
                  key={key}
                  className={`theme-option ${currentTheme === key ? 'active' : ''}`}
                  onClick={() => onThemeChange(key)}
                >
                  <div className="theme-colors">
                    {theme.colors.slice(0, 4).map((color, index) => (
                      <div 
                        key={index}
                        className="color-dot"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                  <div className="theme-info">
                    <div className="theme-name">{theme.name}</div>
                    <div className="theme-desc">{theme.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="customizer-section">
            <h4>차트 크기</h4>
            <div className="size-options">
              {Object.entries(sizes).map(([key, size]) => (
                <button
                  key={key}
                  className={`size-option ${currentSize === key ? 'active' : ''}`}
                  onClick={() => onSizeChange(key)}
                >
                  <span className="size-name">{size.name}</span>
                  <span className="size-desc">{size.description}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VisualizationCustomizer;