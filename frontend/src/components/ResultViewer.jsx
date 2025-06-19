// frontend/src/components/ResultViewer.jsx
import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';
import AdvancedVisualization from './AdvancedVisualization';
import './AdvancedVisualization.css';

// Chart.js 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const ResultViewer = ({ result }) => {
  if (!result) return null;

  // 차트 렌더러
  const ChartRenderer = ({ type, data, title }) => {
    if (!data || !data.labels || !data.datasets) {
      return (
        <div className="chart-error">
          ⚠️ 차트 데이터가 올바르지 않습니다
          <details style={{ marginTop: '10px' }}>
            <summary>데이터 확인</summary>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </details>
        </div>
      );
    }

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: !!title,
          text: title,
          font: { size: 16, weight: 'bold' },
          padding: { bottom: 20 }
        },
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            padding: 20,
            usePointStyle: true
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: 'white',
          bodyColor: 'white',
          borderColor: '#6366f1',
          borderWidth: 1,
          cornerRadius: 8
        }
      },
      scales: type !== 'pie_chart' ? {
        x: {
          grid: { display: false },
          ticks: { color: '#666' }
        },
        y: {
          grid: { color: '#f0f0f0' },
          ticks: { color: '#666' },
          beginAtZero: true
        }
      } : undefined
    };

    const ChartComponent = {
      'bar_chart': Bar,
      'line_chart': Line,
      'pie_chart': Pie
    }[type] || Bar;

    return (
      <div className="chart-container">
        <ChartComponent data={data} options={chartOptions} height={300} />
      </div>
    );
  };

  // 마인드맵 렌더러
  const MindMapRenderer = ({ title, data }) => {
    if (!data || !data.center) {
      return (
        <div className="mindmap-error">
          ⚠️ 마인드맵 데이터가 올바르지 않습니다
          <details style={{ marginTop: '10px' }}>
            <summary>데이터 확인</summary>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </details>
        </div>
      );
    }

    const { center, branches = [] } = data;

    return (
      <div className="mindmap-container">
        {title && <h4 className="mindmap-title">{title}</h4>}

        <div className="mindmap-content">
          {/* 중심 노드 */}
          <div className="center-node">{center}</div>

          {/* 브랜치들 */}
          <div className="branches">
            {branches.map((branch, index) => (
              <div key={index} className="branch">
                <div className="branch-label">{branch.label}</div>
                {branch.children && branch.children.length > 0 && (
                  <div className="children">
                    {branch.children.map((child, childIndex) => (
                      <div key={childIndex} className="child-node">
                        {child}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // 섹션 렌더러
  const renderSection = (section, index) => {
    const { type, title, content, data } = section;

    const sectionProps = {
      key: index,
      className: `section ${type}-section`,
      'data-section-type': type
    };

    switch (type) {
      case 'heading':
        return (
          <div {...sectionProps}>
            <div className="heading-content">
              <h3>{title}</h3>
              {content && <p className="heading-description">{content}</p>}
            </div>
          </div>
        );

      case 'paragraph':
        return (
          <div {...sectionProps}>
            {title && <h4 className="paragraph-title">{title}</h4>}
            <div className="paragraph-content">
              {content?.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          </div>
        );

      case 'bar_chart':
      case 'line_chart':
      case 'pie_chart':
      case 'scatter_plot':
      case 'timeline':
      case 'comparison_table':
      case 'process_flow':
      case 'gauge_chart':
        return (
          <div {...sectionProps}>
            <div className="chart-section">
              <AdvancedVisualization type={type} data={data} title={title} />
            </div>
          </div>
        );

      case 'mindmap':
        return (
          <div {...sectionProps}>
            <div className="mindmap-section">
              <MindMapRenderer title={title} data={data} />
            </div>
          </div>
        );

      default:
        return (
          <div {...sectionProps}>
            <div className="unknown-section">
              <h4>{title || '알 수 없는 섹션'}</h4>
              <p>{content || '지원되지 않는 섹션 타입입니다.'}</p>

              <details className="debug-info">
                <summary>섹션 데이터 (디버그)</summary>
                <pre>{JSON.stringify(section, null, 2)}</pre>
              </details>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="result-viewer">
      <div className="result-header">
        <h3 className="result-title">📊 {result.title}</h3>
        {result.created_at && (
          <div className="result-meta">
            <span className="created-time">
              📅 {new Date(result.created_at).toLocaleString()}
            </span>
          </div>
        )}
      </div>

      <div className="sections">
        {result.sections && result.sections.length > 0 ? (
          result.sections.map((section, index) => renderSection(section, index))
        ) : (
          <div className="no-sections">
            <p>표시할 섹션이 없습니다.</p>
            <details>
              <summary>결과 데이터 확인</summary>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultViewer;