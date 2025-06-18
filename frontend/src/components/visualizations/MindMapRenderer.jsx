// frontend/src/components/visualizations/MindMapRenderer.jsx
import React from 'react';

const MindMapRenderer = ({ title, data }) => {
  if (!data || !data.center) {
    return (
      <div className="mindmap-error">
        <p>마인드맵 데이터가 올바르지 않습니다</p>
      </div>
    );
  }

  const { center, branches = [] } = data;

  return (
    <div className="mindmap-container">
      <h4 style={{ textAlign: 'center', marginBottom: '20px', color: '#333' }}>
        {title}
      </h4>

      <div className="mindmap-svg-container" style={{
        position: 'relative',
        width: '100%',
        height: '400px',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        borderRadius: '12px'
      }}>

        {/* 중심 노드 */}
        <div
          className="center-node"
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '15px 25px',
            borderRadius: '50px',
            fontWeight: 'bold',
            fontSize: '16px',
            boxShadow: '0 8px 20px rgba(102, 126, 234, 0.3)',
            zIndex: 10,
            minWidth: '120px',
            textAlign: 'center'
          }}
        >
          {center}
        </div>

        {/* 가지들 */}
        {branches.map((branch, index) => {
          const angle = (360 / branches.length) * index;
          const radian = (angle * Math.PI) / 180;
          const radius = 150;
          const x = 50 + (radius / 4) * Math.cos(radian);
          const y = 50 + (radius / 4) * Math.sin(radian);

          return (
            <div key={index}>
              {/* 연결선 */}
              <svg
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  pointerEvents: 'none',
                  zIndex: 1
                }}
              >
                <line
                  x1="50%"
                  y1="50%"
                  x2={`${x}%`}
                  y2={`${y}%`}
                  stroke="#667eea"
                  strokeWidth="3"
                  strokeDasharray="5,5"
                  opacity="0.6"
                />
              </svg>

              {/* 주 가지 노드 */}
              <div
                style={{
                  position: 'absolute',
                  top: `${y}%`,
                  left: `${x}%`,
                  transform: 'translate(-50%, -50%)',
                  background: '#ffffff',
                  border: '3px solid #667eea',
                  color: '#333',
                  padding: '10px 15px',
                  borderRadius: '20px',
                  fontWeight: '600',
                  fontSize: '14px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  zIndex: 5,
                  minWidth: '100px',
                  textAlign: 'center'
                }}
              >
                {branch.label}
              </div>

              {/* 세부 항목들 */}
              {branch.children && branch.children.map((child, childIndex) => {
                const childAngle = angle + (childIndex - (branch.children.length - 1) / 2) * 20;
                const childRadian = (childAngle * Math.PI) / 180;
                const childRadius = 200;
                const childX = 50 + (childRadius / 4) * Math.cos(childRadian);
                const childY = 50 + (childRadius / 4) * Math.sin(childRadian);

                return (
                  <div key={childIndex}>
                    {/* 세부 연결선 */}
                    <svg
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        pointerEvents: 'none',
                        zIndex: 1
                      }}
                    >
                      <line
                        x1={`${x}%`}
                        y1={`${y}%`}
                        x2={`${childX}%`}
                        y2={`${childY}%`}
                        stroke="#ec4899"
                        strokeWidth="2"
                        opacity="0.5"
                      />
                    </svg>

                    {/* 세부 노드 */}
                    <div
                      style={{
                        position: 'absolute',
                        top: `${childY}%`,
                        left: `${childX}%`,
                        transform: 'translate(-50%, -50%)',
                        background: 'linear-gradient(135deg, #ec4899 0%, #f093fb 100%)',
                        color: 'white',
                        padding: '6px 12px',
                        borderRadius: '15px',
                        fontSize: '12px',
                        fontWeight: '500',
                        boxShadow: '0 2px 8px rgba(236, 72, 153, 0.3)',
                        zIndex: 3,
                        textAlign: 'center',
                        minWidth: '80px'
                      }}
                    >
                      {child}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MindMapRenderer;