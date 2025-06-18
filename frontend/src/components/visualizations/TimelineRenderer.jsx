// frontend/src/components/visualizations/TimelineRenderer.jsx
import React from 'react';

export const TimelineRenderer = ({ title, data }) => {
  if (!data || !data.events) {
    return (
      <div className="timeline-error">
        <p>타임라인 데이터가 올바르지 않습니다</p>
      </div>
    );
  }

  const { events = [] } = data;

  return (
    <div className="timeline-container">
      <h4 style={{ textAlign: 'center', marginBottom: '30px', color: '#333' }}>
        {title}
      </h4>

      <div className="timeline-content" style={{
        position: 'relative',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        padding: '20px',
        borderRadius: '12px'
      }}>
        {/* 중앙 라인 */}
        <div style={{
          position: 'absolute',
          left: '50%',
          top: '20px',
          bottom: '20px',
          width: '4px',
          background: 'linear-gradient(180deg, #6366f1 0%, #ec4899 100%)',
          transform: 'translateX(-50%)',
          borderRadius: '2px'
        }} />

        {events.map((event, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '40px',
              position: 'relative'
            }}
          >
            {/* 짝수는 왼쪽, 홀수는 오른쪽 */}
            {index % 2 === 0 ? (
              <>
                {/* 왼쪽 컨텐츠 */}
                <div style={{
                  flex: '1',
                  textAlign: 'right',
                  paddingRight: '30px'
                }}>
                  <div style={{
                    background: 'white',
                    padding: '15px',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    border: '2px solid #6366f1'
                  }}>
                    <div style={{
                      background: '#6366f1',
                      color: 'white',
                      padding: '5px 10px',
                      borderRadius: '15px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      display: 'inline-block',
                      marginBottom: '8px'
                    }}>
                      {event.time}
                    </div>
                    <h5 style={{ margin: '0 0 8px 0', color: '#333' }}>
                      {event.title}
                    </h5>
                    <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
                      {event.description}
                    </p>
                  </div>
                </div>

                {/* 중앙 점 */}
                <div style={{
                  width: '16px',
                  height: '16px',
                  background: '#6366f1',
                  borderRadius: '50%',
                  border: '4px solid white',
                  boxShadow: '0 2px 8px rgba(99, 102, 241, 0.3)',
                  zIndex: 10,
                  position: 'relative'
                }} />

                {/* 오른쪽 빈 공간 */}
                <div style={{ flex: '1' }} />
              </>
            ) : (
              <>
                {/* 왼쪽 빈 공간 */}
                <div style={{ flex: '1' }} />

                {/* 중앙 점 */}
                <div style={{
                  width: '16px',
                  height: '16px',
                  background: '#ec4899',
                  borderRadius: '50%',
                  border: '4px solid white',
                  boxShadow: '0 2px 8px rgba(236, 72, 153, 0.3)',
                  zIndex: 10,
                  position: 'relative'
                }} />

                {/* 오른쪽 컨텐츠 */}
                <div style={{
                  flex: '1',
                  textAlign: 'left',
                  paddingLeft: '30px'
                }}>
                  <div style={{
                    background: 'white',
                    padding: '15px',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    border: '2px solid #ec4899'
                  }}>
                    <div style={{
                      background: '#ec4899',
                      color: 'white',
                      padding: '5px 10px',
                      borderRadius: '15px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      display: 'inline-block',
                      marginBottom: '8px'
                    }}>
                      {event.time}
                    </div>
                    <h5 style={{ margin: '0 0 8px 0', color: '#333' }}>
                      {event.title}
                    </h5>
                    <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
                      {event.description}
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// frontend/src/components/visualizations/ComparisonRenderer.jsx
export const ComparisonRenderer = ({ title, data }) => {
  if (!data || !data.items || !data.criteria) {
    return (
      <div className="comparison-error">
        <p>비교표 데이터가 올바르지 않습니다</p>
      </div>
    );
  }

  const { items = [], criteria = [], values = [] } = data;

  return (
    <div className="comparison-container">
      <h4 style={{ textAlign: 'center', marginBottom: '20px', color: '#333' }}>
        {title}
      </h4>

      <div style={{
        background: 'white',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '14px'
        }}>
          <thead>
            <tr style={{ background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' }}>
              <th style={{
                padding: '15px',
                color: 'white',
                fontWeight: '600',
                textAlign: 'left',
                borderRight: '1px solid rgba(255,255,255,0.2)'
              }}>
                항목 / 기준
              </th>
              {criteria.map((criterion, index) => (
                <th key={index} style={{
                  padding: '15px',
                  color: 'white',
                  fontWeight: '600',
                  textAlign: 'center',
                  borderRight: index < criteria.length - 1 ? '1px solid rgba(255,255,255,0.2)' : 'none'
                }}>
                  {criterion}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((item, rowIndex) => (
              <tr key={rowIndex} style={{
                background: rowIndex % 2 === 0 ? '#f8fafc' : 'white',
                borderBottom: '1px solid #e2e8f0'
              }}>
                <td style={{
                  padding: '15px',
                  fontWeight: '600',
                  color: '#333',
                  background: 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
                  borderRight: '2px solid #6366f1'
                }}>
                  {item}
                </td>
                {criteria.map((_, colIndex) => (
                  <td key={colIndex} style={{
                    padding: '15px',
                    textAlign: 'center',
                    color: '#555',
                    borderRight: colIndex < criteria.length - 1 ? '1px solid #e2e8f0' : 'none'
                  }}>
                    {values[rowIndex] && values[rowIndex][colIndex] ? (
                      <span style={{
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '500'
                      }}>
                        {values[rowIndex][colIndex]}
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// frontend/src/components/visualizations/TreeRenderer.jsx
export const TreeRenderer = ({ title, data }) => {
  if (!data || !data.root) {
    return (
      <div className="tree-error">
        <p>트리 데이터가 올바르지 않습니다</p>
      </div>
    );
  }

  const renderNode = (node, level = 0) => {
    if (typeof node === 'string') {
      return (
        <div style={{
          background: level === 0 ? 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' :
                     level === 1 ? 'linear-gradient(135deg, #ec4899 0%, #f093fb 100%)' :
                     'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          color: 'white',
          padding: '8px 15px',
          margin: '5px',
          borderRadius: level === 0 ? '25px' : '15px',
          fontSize: level === 0 ? '16px' : level === 1 ? '14px' : '12px',
          fontWeight: level === 0 ? '700' : '500',
          textAlign: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          minWidth: level === 0 ? '150px' : '100px'
        }}>
          {node}
        </div>
      );
    }

    return (
      <div style={{ textAlign: 'center', margin: '10px 0' }}>
        <div style={{
          background: level === 0 ? 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' :
                     level === 1 ? 'linear-gradient(135deg, #ec4899 0%, #f093fb 100%)' :
                     'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          color: 'white',
          padding: '10px 20px',
          margin: '5px auto',
          borderRadius: level === 0 ? '25px' : '15px',
          fontSize: level === 0 ? '16px' : level === 1 ? '14px' : '12px',
          fontWeight: level === 0 ? '700' : '500',
          display: 'inline-block',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
          minWidth: level === 0 ? '150px' : '100px'
        }}>
          {node.label}
        </div>

        {node.children && node.children.length > 0 && (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            flexWrap: 'wrap',
            gap: '10px',
            marginTop: '15px'
          }}>
            {node.children.map((child, index) => (
              <div key={index}>
                {renderNode(child, level + 1)}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="tree-container">
      <h4 style={{ textAlign: 'center', marginBottom: '20px', color: '#333' }}>
        {title}
      </h4>

      <div style={{
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        padding: '30px',
        borderRadius: '12px',
        overflow: 'auto'
      }}>
        {renderNode({ label: data.root, children: data.children }, 0)}
      </div>
    </div>
  );
};

// frontend/src/components/visualizations/NetworkRenderer.jsx
export const NetworkRenderer = ({ title, data }) => {
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

export default { TimelineRenderer, ComparisonRenderer, TreeRenderer, NetworkRenderer };