// frontend/src/components/SmartVisualization.jsx
import React, { useEffect, useRef, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Bar, Line, Pie, Doughnut, Radar, Scatter } from 'react-chartjs-2';

// Chart.js 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Mermaid 동적 로드
let mermaidLoaded = false;
const loadMermaid = async () => {
  if (!mermaidLoaded && !window.mermaid) {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
    script.async = true;
    script.onload = () => {
      window.mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        flowchart: {
          htmlLabels: true,
          curve: 'linear'
        }
      });
      mermaidLoaded = true;
    };
    document.head.appendChild(script);
  }
};

const SmartVisualization = ({ section }) => {
  const [error, setError] = useState(null);
  const chartRef = useRef(null);
  const mermaidRef = useRef(null);

  useEffect(() => {
    // Mermaid 다이어그램 렌더링
    if (section.data?.type === 'diagram' && section.data?.code && mermaidRef.current) {
      loadMermaid().then(() => {
        if (window.mermaid && mermaidRef.current) {
          try {
            mermaidRef.current.innerHTML = section.data.code;
            window.mermaid.init(undefined, mermaidRef.current);
          } catch (err) {
            console.error('Mermaid 렌더링 오류:', err);
            setError('다이어그램 렌더링 실패');
          }
        }
      });
    }
  }, [section]);

  if (section.error) {
    return (
      <div className="visualization-error">
        <p>⚠️ {section.error}</p>
      </div>
    );
  }

  if (!section.data) {
    return (
      <div className="visualization-error">
        <p>⚠️ 시각화 데이터가 없습니다</p>
      </div>
    );
  }

  const renderChart = () => {
    const { config } = section.data;
    if (!config) return null;

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: section.title
        }
      },
      ...config.options
    };

    const chartProps = {
      data: config.data,
      options: chartOptions,
      ref: chartRef
    };

    switch (config.type) {
      case 'bar':
        return <Bar {...chartProps} />;
      case 'line':
        return <Line {...chartProps} />;
      case 'pie':
        return <Pie {...chartProps} />;
      case 'doughnut':
        return <Doughnut {...chartProps} />;
      case 'radar':
        return <Radar {...chartProps} />;
      case 'scatter':
        return <Scatter {...chartProps} />;
      default:
        return <div>지원하지 않는 차트 타입: {config.type}</div>;
    }
  };

  const renderTable = () => {
    const { headers, rows, styling } = section.data;
    if (!headers || !rows) return null;

    return (
      <div className="table-container">
        <table className={`data-table ${styling?.sortable ? 'sortable' : ''}`}>
          <thead>
            <tr>
              {headers.map((header, i) => (
                <th key={i} className={styling?.highlight_column === i ? 'highlighted' : ''}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className={styling?.highlight_column === cellIndex ? 'highlighted' : ''}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderAdvanced = () => {
    // D3.js 또는 기타 고급 시각화는 별도 구현 필요
    return (
      <div className="advanced-visualization-placeholder">
        <h4>{section.data.visualization_type} 시각화</h4>
        <p>고급 시각화는 추가 구현이 필요합니다.</p>
        <pre>{JSON.stringify(section.data.data, null, 2)}</pre>
      </div>
    );
  };

  const getPurposeIcon = (purpose) => {
    const icons = {
      overview: '🌐',
      detail: '🔍',
      comparison: '⚖️',
      process: '🔄',
      data: '📊',
      timeline: '📅',
      structure: '🏗️'
    };
    return icons[purpose] || '📊';
  };

  const getPurposeLabel = (purpose) => {
    const labels = {
      overview: '전체 개요',
      detail: '세부 분석',
      comparison: '비교',
      process: '프로세스',
      data: '데이터',
      timeline: '타임라인',
      structure: '구조'
    };
    return labels[purpose] || purpose;
  };

  return (
    <div className="smart-visualization">
      <div className="visualization-header">
        <h3>
          {getPurposeIcon(section.purpose)} {section.title}
          {section.purpose && (
            <span className={`purpose-badge purpose-${section.purpose}`}>
              {getPurposeLabel(section.purpose)}
            </span>
          )}
        </h3>
      </div>

      <div className="visualization-content">
        {error ? (
          <div className="visualization-error">
            <p>⚠️ {error}</p>
          </div>
        ) : (
          <>
            {section.data.type === 'chart' && (
              <div className="chart-container">
                {renderChart()}
              </div>
            )}

            {section.data.type === 'diagram' && (
              <div className="diagram-container">
                <div ref={mermaidRef} className="mermaid"></div>
              </div>
            )}

            {section.data.type === 'table' && renderTable()}

            {section.data.type === 'advanced' && renderAdvanced()}
          </>
        )}
      </div>

      {section.insight && (
        <div className="visualization-insight">
          <h4>💡 핵심 인사이트</h4>
          <p>{section.insight}</p>
        </div>
      )}

      {section.user_benefit && (
        <div className="visualization-benefit">
          <h4>🎯 이 시각화의 가치</h4>
          <p>{section.user_benefit}</p>
        </div>
      )}
    </div>
  );
};

export default SmartVisualization;