// frontend/src/components/visualizations/FlowChartRenderer.jsx
import React from 'react';

const FlowChartRenderer = ({ title, data }) => {
  if (!data || !data.nodes) {
    return (
      <div className="flowchart-error">
        <p>플로우차트 데이터가 올바르지 않습니다</p>
      </div>
    );
  }

  const { nodes = [], edges = [] } = data;

  // 노드 타입별 스타일
  const getNodeStyle = (nodeType) => {
    const baseStyle = {
      padding: '12px 20px',
      margin: '10px',
      borderRadius: '8px',
      color: 'white',
      fontWeight: '600',
      fontSize: '14px',
      textAlign: 'center',
      minWidth: '120px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
      position: 'relative',
      zIndex: 5
    };

    switch (nodeType) {
      case 'start':
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          borderRadius: '50px'
        };
      case 'end':
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
          borderRadius: '50px'
        };
      case 'decision':
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
          borderRadius: '0',
          transform: 'rotate(45deg)',
          width: '80px',
          height: '80px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        };
      case 'process':
      default:
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
          borderRadius: '8px'
        };
    }
  };

  // 화살표 컴포넌트
  const Arrow = ({ from, to, nodes }) => {
    if (!from || !to) return null;

    return (
      <div className="arrow" style={{
        position: 'absolute',
        zIndex: 2,
        color: '#666',
        fontSize: '24px'
      }}>
        ↓
      </div>
    );
  };

  return (
    <div className="flowchart-container">
      <h4 style={{ textAlign: 'center', marginBottom: '20px', color: '#333' }}>
        {title}
      </h4>

      <div
        className="flowchart-content"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
          padding: '30px',
          borderRadius: '12px',
          minHeight: '300px',
          position: 'relative'
        }}
      >
        {nodes.map((node, index) => (
          <div key={node.id || index}>
            {/* 노드 */}
            <div style={getNodeStyle(node.type)}>
              {node.type === 'decision' ? (
                <div style={{ transform: 'rotate(-45deg)' }}>
                  {node.label}
                </div>
              ) : (
                node.label
              )}
            </div>

            {/* 화살표 (마지막 노드가 아닌 경우) */}
            {index < nodes.length - 1 && (
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                margin: '5px 0',
                fontSize: '20px',
                color: '#6366f1'
              }}>
                ↓
              </div>
            )}
          </div>
        ))}

        {/* 복잡한 연결이 있는 경우 edges 정보 표시 */}
        {edges.length > 0 && edges.length !== nodes.length - 1 && (
          <div style={{
            marginTop: '20px',
            padding: '15px',
            background: 'rgba(255,255,255,0.8)',
            borderRadius: '8px',
            fontSize: '12px'
          }}>
            <strong>연결 정보:</strong>
            <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
              {edges.map((edge, index) => (
                <li key={index}>
                  {edge.from} → {edge.to}
                  {edge.label && ` (${edge.label})`}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default FlowChartRenderer;