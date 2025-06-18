// frontend/src/components/visualizations/NetworkRenderer.jsx
import React from 'react';

const NetworkRenderer = ({ title, data }) => {
  if (!data || !data.nodes) {
    return (
      <div className="network-error">
        <p>네트워크 데이터가 올바르지 않습니다</p>
      </div>
    );
  }

  const { nodes = [], links = [] } = data;

  return (
    <div className="network-container">
      <h4 style={{ textAlign: 'center', marginBottom: '20px', color: '#333' }}>
        {title}
      </h4>

      <div style={{
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        padding: '20px',
        borderRadius: '12px',
        height: '300px',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* 간단한 네트워크 시각화 */}
        {nodes.map((node, index) => {
          const angle = (360 / nodes.length) * index;
          const radian = (angle * Math.PI) / 180;
          const radius = 100;
          const x = 50 + (radius / 2) * Math.cos(radian);
          const y = 50 + (radius / 2) * Math.sin(radian);

          return (
            <div
              key={node.id || index}
              style={{
                position: 'absolute',
                top: `${y}%`,
                left: `${x}%`,
                transform: 'translate(-50%, -50%)',
                background: `linear-gradient(135deg, ${node.color || '#6366f1'} 0%, ${node.color || '#4f46e5'} 100%)`,
                color: 'white',
                padding: '10px 15px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: '600',
                textAlign: 'center',
                boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                zIndex: 10,
                minWidth: '80px'
              }}
            >
              {node.label || node.name}
            </div>
          );
        })}

        {/* 연결선들 (간단한 표현) */}
        <svg style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none'
        }}>
          {links.map((link, index) => (
            <line
              key={index}
              x1="50%"
              y1="50%"
              x2="50%"
              y2="50%"
              stroke="#666"
              strokeWidth="2"
              opacity="0.3"
            />
          ))}
        </svg>

        {/* 연결 정보 텍스트 */}
        <div style={{
          position: 'absolute',
          bottom: '10px',
          left: '10px',
          background: 'rgba(255,255,255,0.9)',
          padding: '8px 12px',
          borderRadius: '8px',
          fontSize: '11px',
          color: '#666'
        }}>
          노드: {nodes.length}개 | 연결: {links.length}개
        </div>
      </div>
    </div>
  );
};

export default NetworkRenderer;