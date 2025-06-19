import React, { useState } from 'react';

const VisualizationCustomizer = ({ onThemeChange, onSizeChange, currentTheme, currentSize }) => {
  const [isOpen, setIsOpen] = useState(false);

  const themes = {
    website: { name: '웹사이트', colors: ['#667eea', '#764ba2', '#ec4899'] },
    professional: { name: '프로페셔널', colors: ['#3b82f6', '#10b981', '#f59e0b'] },
    warm: { name: '따뜻한', colors: ['#f59e0b', '#ef4444', '#f97316'] },
    cool: { name: '차가운', colors: ['#06b6d4', '#0891b2', '#3b82f6'] },
    nature: { name: '자연', colors: ['#10b981', '#059669', '#84cc16'] }
  };

  const sizes = {
    compact: '컴팩트',
    normal: '보통',
    large: '크게'
  };

  if (!isOpen) {
    return (
      <button 
        className="customize-btn"
        onClick={() => setIsOpen(true)}
        title="스타일 변경"
      >
        🎨 스타일
      </button>
    );
  }

  return (
    <div className="visualization-customizer">
      <div className="customizer-header">
        <h4>스타일 설정</h4>
        <button onClick={() => setIsOpen(false)} className="close-btn">✕</button>
      </div>

      <div className="customizer-content">
        <div className="theme-section">
          <h5>테마</h5>
          <div className="theme-options">
            {Object.entries(themes).map(([key, theme]) => (
              <div 
                key={key}
                className={`theme-option ${currentTheme === key ? 'active' : ''}`}
                onClick={() => onThemeChange(key)}
              >
                <div className="theme-name">{theme.name}</div>
                <div className="theme-colors">
                  {theme.colors.map((color, i) => (
                    <div 
                      key={i}
                      className="color-dot"
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="size-section">
          <h5>크기</h5>
          <div className="size-options">
            {Object.entries(sizes).map(([key, name]) => (
              <button
                key={key}
                className={`size-option ${currentSize === key ? 'active' : ''}`}
                onClick={() => onSizeChange(key)}
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VisualizationCustomizer;