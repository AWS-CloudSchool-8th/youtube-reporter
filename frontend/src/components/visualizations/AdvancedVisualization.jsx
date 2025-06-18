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
  console.log(`🎨 섹션 ${index} 렌더링:`, {
    type: section.type,
    title: section.title,
    hasData: !!section.data,
    dataKeys: section.data ? Object.keys(section.data) : [],
    hasContent: !!section.content
  });

  const renderVisualization = () => {
    const { type, title, data, content } = section;

    // 🔑 각 타입별 컴포넌트 직접 렌더링 (import 에러 방지)
    switch (type) {
      // 기본 차트
      case 'bar_chart':
      case 'line_chart':
      case 'pie_chart':
        console.log(`📊 기본 차트 렌더링: ${type}`);
        return (
          <ChartRenderer
            type={type}
            data={data}
            title={title}
          />
        );

      // 마인드맵
      case 'mindmap':
        console.log(`🗺️ 마인드맵 렌더링`);
        if (!data || !data.center) {
          return (
            <div className="mindmap-error">
              <p>⚠️ 마인드맵 데이터가 올바르지 않습니다</p>
            </div>
          );
        }
        return (
          <MindMapRenderer
            title={title}
            data={data}
          />
        );

      // 플로우차트
      case 'flowchart':
      case 'process':
        console.log(`📊 플로우차트 렌더링: ${type}`);
        if (!data || !data.nodes) {
          return (
            <div className="flowchart-error">
              <p>⚠️ 플로우차트 데이터가 올바르지 않습니다</p>
            </div>
          );
        }
        return (
          <FlowChartRenderer
            title={title}
            data={data}
          />
        );

      // 타임라인
      case 'timeline':
        console.log(`⏰ 타임라인 렌더링`);
        if (!data || !data.events) {
          return (
            <div className="timeline-error">
              <p>⚠️ 타임라인 데이터가 올바르지 않습니다</p>
            </div>
          );
        }
        return (
          <TimelineRenderer
            title={title}
            data={data}
          />
        );

      // 비교표
      case 'comparison':
      case 'matrix':
        console.log(`📋 비교표 렌더링: ${type}`);
        if (!data || !data.items || !data.criteria) {
          return (
            <div className="comparison-error">
              <p>⚠️ 비교표 데이터가 올바르지 않습니다</p>
            </div>
          );
        }
        return (
          <ComparisonRenderer
            title={title}
            data={data}
          />
        );

      // 트리/계층구조
      case 'tree':
      case 'hierarchy':
        console.log(`🌳 트리 렌더링: ${type}`);
        if (!data || !data.root) {
          return (
            <div className="tree-error">
              <p>⚠️ 트리 데이터가 올바르지 않습니다</p>
            </div>
          );
        }
        return (
          <TreeRenderer
            title={title}
            data={data}
          />
        );

      // 네트워크
      case 'network':
        console.log(`🕸️ 네트워크 렌더링`);
        if (!data || !data.nodes) {
          return (
            <div className="network-error">
              <p>⚠️ 네트워크 데이터가 올바르지 않습니다</p>
            </div>
          );
        }
        return (
          <NetworkRenderer
            title={title}
            data={data}
          />
        );

      // 사이클 - 직접 렌더링 (별도 컴포넌트 없이)
      case 'cycle':
        console.log(`🔄 사이클 렌더링`);
        return (
          <div className="cycle-visualization" style={{
            background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
            padding: '20px',
            borderRadius: '12px'
          }}>
            <h4 style={{ textAlign: 'center', marginBottom: '20px' }}>{title}</h4>
            <div className="cycle-container" style={{
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'center',
              gap: '15px'
            }}>
              {data?.steps ? data.steps.map((step, idx) => (
                <div key={idx} className="cycle-step" style={{
                  background: 'white',
                  border: '2px solid #6366f1',
                  borderRadius: '50%',
                  width: '80px',
                  height: '80px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                  fontSize: '12px'
                }}>
                  <div style={{
                    background: '#6366f1',
                    color: 'white',
                    borderRadius: '50%',
                    width: '20px',
                    height: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '10px',
                    fontWeight: 'bold',
                    marginBottom: '5px'
                  }}>
                    {idx + 1}
                  </div>
                  <div style={{ fontSize: '9px' }}>
                    {step}
                  </div>
                </div>
              )) : (
                <p>사이클 단계 데이터가 없습니다.</p>
              )}
            </div>
          </div>
        );

      // 텍스트 섹션
      case 'paragraph':
        console.log(`📝 단락 렌더링`);
        return (
          <div className="paragraph-section">
            {title && <h4>{title}</h4>}
            <p>{content || '내용이 없습니다.'}</p>
          </div>
        );

      case 'heading':
        console.log(`📋 제목 렌더링`);
        return (
          <div className="heading-section">
            <h3>{title || content || '제목이 없습니다.'}</h3>
          </div>
        );

      default:
        console.warn(`🔧 지원되지 않는 시각화 타입: ${type}`);
        return (
          <div className="unknown-visualization">
            <h4>🔧 {title}</h4>
            <p style={{ marginBottom: '15px' }}>
              지원되지 않는 시각화 타입: <strong>{type}</strong>
            </p>
            <div style={{
              background: '#e3f2fd',
              padding: '15px',
              borderRadius: '8px',
              marginBottom: '15px'
            }}>
              <p style={{ margin: 0, color: '#1565c0' }}>
                💡 이 타입은 곧 지원될 예정입니다. 현재는 원본 데이터를 표시합니다.
              </p>
            </div>
            <details>
              <summary style={{
                cursor: 'pointer',
                fontWeight: 'bold',
                background: '#f5f5f5',
                padding: '10px',
                borderRadius: '4px',
                marginBottom: '10px'
              }}>
                원본 데이터 보기
              </summary>
              <pre style={{
                fontSize: '10px',
                background: '#f5f5f5',
                padding: '10px',
                borderRadius: '4px',
                overflow: 'auto',
                maxHeight: '300px'
              }}>
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
          padding: '8px',
          background: '#f0f0f0',
          borderRadius: '4px',
          fontFamily: 'monospace'
        }}>
          <strong>디버그:</strong> 섹션 {index + 1} | 타입: {section.type} |
          데이터: {section.data ? `있음 (${Object.keys(section.data).length}개 키)` : '없음'} |
          내용: {section.content ? `있음 (${section.content.length}자)` : '없음'}
        </div>
      )}

      {renderVisualization()}
    </div>
  );
};

export default AdvancedVisualization;