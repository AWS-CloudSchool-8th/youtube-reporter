// frontend/src/components/visualizations/AdvancedVisualization.jsx
import React from 'react';
import ChartRenderer from '../charts/ChartRenderer.jsx';
import MindMapRenderer from './MindMapRenderer.jsx';
import FlowChartRenderer from './FlowChartRenderer.jsx';
import TimelineRenderer from './TimelineRenderer.jsx';
import ComparisonRenderer from './ComparisonRenderer.jsx';
import TreeRenderer from './TreeRenderer.jsx';
import NetworkRenderer from './NetworkRenderer.jsx';

const AdvancedVisualization = ({ section, index }) => {
  const renderVisualization = () => {
    const { type, title, data } = section;

    // 데이터 검증
    if (!data) {
      return (
        <div className="visualization-error">
          <p>⚠️ 시각화 데이터가 없습니다</p>
          <pre style={{ fontSize: '10px', color: '#666' }}>
            {JSON.stringify(section, null, 2)}
          </pre>
        </div>
      );
    }

    // 각 시각화 타입별 렌더링
    switch (type) {
      // 기본 차트
      case 'bar_chart':
      case 'line_chart':
      case 'pie_chart':
        return (
          <ChartRenderer
            type={type}
            data={data}
            title={title}
          />
        );

      // 마인드맵
      case 'mindmap':
        return (
          <MindMapRenderer
            title={title}
            data={data}
          />
        );

      // 플로우차트
      case 'flowchart':
      case 'process':
        return (
          <FlowChartRenderer
            title={title}
            data={data}
          />
        );

      // 타임라인
      case 'timeline':
        return (
          <TimelineRenderer
            title={title}
            data={data}
          />
        );

      // 비교표
      case 'comparison':
      case 'matrix':
        return (
          <ComparisonRenderer
            title={title}
            data={data}
          />
        );

      // 트리/계층구조
      case 'tree':
      case 'hierarchy':
        return (
          <TreeRenderer
            title={title}
            data={data}
          />
        );

      // 네트워크
      case 'network':
        return (
          <NetworkRenderer
            title={title}
            data={data}
          />
        );

      // 사이클
      case 'cycle':
        return (
          <div className="cycle-visualization">
            <h4>{title}</h4>
            <div className="cycle-container">
              {data.steps && data.steps.map((step, idx) => (
                <div key={idx} className="cycle-step">
                  <div className="step-number">{idx + 1}</div>
                  <div className="step-content">{step}</div>
                </div>
              ))}
            </div>
          </div>
        );

      // 텍스트 섹션
      case 'paragraph':
        return (
          <div className="paragraph-section">
            {title && <h4>{title}</h4>}
            <p>{section.content}</p>
          </div>
        );

      case 'heading':
        return (
          <div className="heading-section">
            <h3>{title || section.content}</h3>
          </div>
        );

      default:
        return (
          <div className="unknown-visualization">
            <h4>{title}</h4>
            <p>🔧 지원되지 않는 시각화 타입: {type}</p>
            <details>
              <summary>원본 데이터 보기</summary>
              <pre style={{ fontSize: '10px', background: '#f5f5f5', padding: '10px' }}>
                {JSON.stringify(section, null, 2)}
              </pre>
            </details>
          </div>
        );
    }
  };

  return (
    <div
      className={`visualization-container ${section.type}`}
      style={{
        margin: '20px 0',
        padding: '20px',
        borderRadius: '12px',
        background: section.type === 'paragraph' || section.type === 'heading'
          ? '#f8f9fa'
          : '#ffffff',
        border: '1px solid #e9ecef',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}
    >
      {/* 섹션 메타 정보 (개발 모드에서만) */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{
          fontSize: '11px',
          color: '#666',
          marginBottom: '10px',
          padding: '5px',
          background: '#f0f0f0',
          borderRadius: '4px'
        }}>
          섹션 {index + 1}: {section.type}
          {section.data && ` | 데이터 키: ${Object.keys(section.data).join(', ')}`}
        </div>
      )}

      {renderVisualization()}
    </div>
  );
};

export default AdvancedVisualization;