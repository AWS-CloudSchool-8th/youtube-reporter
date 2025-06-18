// frontend/src/components/charts/ChartRenderer.jsx
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
  Legend,
  Filler
} from 'chart.js';
import { Bar, Line, Pie, Doughnut } from 'react-chartjs-2';
import { napkinTheme, getChartConfig, generateChartColors } from '../../utils/napkinTheme';

// Chart.js 컴포넌트 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const ChartRenderer = ({ type, data, title, className = "" }) => {
  // 데이터 검증
  if (!data || !data.labels || !data.datasets) {
    return (
      <div className={`chart-error ${className}`}>
        <p>⚠️ 차트 데이터가 올바르지 않습니다</p>
      </div>
    );
  }

  // 차트 설정 가져오기
  const chartConfig = getChartConfig(type);

  // 데이터에 napkin.ai 스타일 적용
  const styledData = {
    ...data,
    datasets: data.datasets.map((dataset, index) => {
      const colors = generateChartColors(data.labels.length);

      return {
        ...dataset,
        backgroundColor: type === 'pie' || type === 'doughnut'
          ? colors
          : dataset.backgroundColor || napkinTheme.colors.primary,
        borderColor: type === 'pie' || type === 'doughnut'
          ? colors.map(color => color)
          : dataset.borderColor || napkinTheme.colors.primaryDark,
        borderWidth: 2,
        // Bar 차트 전용 스타일
        ...(type === 'bar' && {
          borderRadius: 8,
          borderSkipped: false,
        }),
        // Line 차트 전용 스타일
        ...(type === 'line' && {
          tension: 0.2,
          fill: true,
          backgroundColor: `${napkinTheme.colors.primary}20`, // 20% 투명도
        }),
      };
    })
  };

  // 옵션에 제목 추가
  const options = {
    ...chartConfig,
    plugins: {
      ...chartConfig.plugins,
      title: {
        display: !!title,
        text: title,
        color: napkinTheme.colors.text,
        font: {
          size: 16,
          weight: '600',
        },
        padding: {
          bottom: 20,
        }
      }
    }
  };

  // 차트 컴포넌트 선택
  const renderChart = () => {
    const commonProps = {
      data: styledData,
      options: options,
      height: 300
    };

    switch (type) {
      case 'bar_chart':
      case 'bar':
        return <Bar {...commonProps} />;

      case 'line_chart':
      case 'line':
        return <Line {...commonProps} />;

      case 'pie_chart':
      case 'pie':
        return <Pie {...commonProps} height={250} />;

      case 'doughnut':
        return <Doughnut {...commonProps} height={250} />;

      default:
        return <Bar {...commonProps} />;
    }
  };

  return (
    <div className={`chart-container ${className}`} style={{
      background: napkinTheme.colors.background,
      borderRadius: '16px',
      padding: '20px',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
      border: `1px solid ${napkinTheme.colors.border}`,
      position: 'relative',
      height: '350px'
    }}>
      {renderChart()}
    </div>
  );
};

export default ChartRenderer;