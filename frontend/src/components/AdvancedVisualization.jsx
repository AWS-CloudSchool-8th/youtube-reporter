// frontend/src/components/AdvancedVisualization.jsx
import React, { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  ScatterChart, Scatter, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import Plot from 'react-plotly.js';
import VisualizationCustomizer from './VisualizationCustomizer';
import VisualizationEditor from './VisualizationEditor';
import './AdvancedVisualization.css';
import './VisualizationCustomizer.css';
import './VisualizationEditor.css';

const AdvancedVisualization = ({ type, data, title }) => {
  const [theme, setTheme] = useState('website');
  const [size, setSize] = useState('normal');
  const [currentData, setCurrentData] = useState(data);

  if (!currentData) return <div>데이터가 없습니다.</div>;

  // 테마별 색상 팔레트
  const themes = {
    website: ['#667eea', '#764ba2', '#ec4899', '#f093fb', '#6366f1', '#4f46e5'],
    professional: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
    warm: ['#f59e0b', '#ef4444', '#f97316', '#eab308', '#dc2626', '#ea580c'],
    cool: ['#06b6d4', '#0891b2', '#3b82f6', '#1d4ed8', '#6366f1', '#4338ca'],
    nature: ['#10b981', '#059669', '#84cc16', '#65a30d', '#22c55e', '#16a34a']
  };

  const sizes = {
    compact: 250,
    normal: 300,
    large: 400
  };

  const colors = themes[theme];
  const chartHeight = sizes[size];

  // Recharts용 데이터 변환
  const convertToRechartsData = (chartData) => {
    if (!chartData.labels || !chartData.datasets) return [];
    
    return chartData.labels.map((label, index) => {
      const item = { name: label };
      chartData.datasets.forEach((dataset, datasetIndex) => {
        item[dataset.label || `데이터${datasetIndex + 1}`] = dataset.data[index] || 0;
      });
      return item;
    });
  };

  const handleDataChange = (newData) => {
    setCurrentData(newData);
  };

  // Plotly용 데이터 변환
  const convertToPlotlyData = (chartData) => {
    if (!chartData.datasets) return [];
    
    return chartData.datasets.map((dataset, index) => ({
      x: chartData.labels,
      y: dataset.data,
      type: 'scatter',
      mode: 'markers',
      name: dataset.label,
      marker: { color: colors[index % colors.length] }
    }));
  };

  const renderVisualization = () => {
    switch (type) {
      case 'bar_chart':
        const barData = convertToRechartsData(currentData);
        return (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="2 2" stroke="#f3f4f6" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 12, fill: '#6b7280' }}
                axisLine={{ stroke: '#e5e7eb' }}
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#6b7280' }}
                axisLine={{ stroke: '#e5e7eb' }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  fontSize: '12px'
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', color: '#6b7280' }} />
              {currentData.datasets?.map((dataset, index) => (
                <Bar 
                  key={`${theme}-${index}`}
                  dataKey={dataset.label || `데이터${index + 1}`}
                  fill={colors[index % colors.length]}
                  radius={[2, 2, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line_chart':
        const lineData = convertToRechartsData(currentData);
        return (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <LineChart data={lineData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="2 2" stroke="#f3f4f6" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 12, fill: '#6b7280' }}
                axisLine={{ stroke: '#e5e7eb' }}
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#6b7280' }}
                axisLine={{ stroke: '#e5e7eb' }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  fontSize: '12px'
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', color: '#6b7280' }} />
              {currentData.datasets?.map((dataset, index) => (
                <Line 
                  key={`${theme}-${index}`}
                  type="monotone"
                  dataKey={dataset.label || `데이터${index + 1}`}
                  stroke={colors[index % colors.length]}
                  strokeWidth={3}
                  dot={{ r: 4, fill: colors[index % colors.length] }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie_chart':
        const pieData = currentData.labels?.map((label, index) => ({
          name: label,
          value: currentData.datasets?.[0]?.data?.[index] || 0
        })) || [];
        
        return (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={Math.min(chartHeight * 0.3, 120)}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`${theme}-cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  fontSize: '12px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'scatter_plot':
        const scatterData = convertToPlotlyData(data);
        return (
          <Plot
            data={scatterData}
            layout={{
              width: '100%',
              height: 400,
              title: title,
              xaxis: { title: 'X축' },
              yaxis: { title: 'Y축' }
            }}
            config={{ responsive: true }}
          />
        );

      case 'timeline':
        return (
          <div className="timeline-container">
            <h4>{title}</h4>
            <div className="timeline">
              {Array.isArray(currentData.events) ? currentData.events.map((event, index) => (
                <div key={index} className="timeline-item">
                  <div className="timeline-marker"></div>
                  <div className="timeline-content">
                    <div className="timeline-date">{event.date || ''}</div>
                    <div className="timeline-title">{event.title || ''}</div>
                    <div className="timeline-description">{event.description || ''}</div>
                  </div>
                </div>
              )) : <div>타임라인 데이터가 없습니다.</div>}
            </div>
          </div>
        );

      case 'comparison_table':
        return (
          <div className="comparison-table-container">
            <h4>{title}</h4>
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>항목</th>
                  {data.columns?.map((col, index) => (
                    <th key={index}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows?.map((row, index) => (
                  <tr key={index}>
                    <td className="row-header">{row.name}</td>
                    {Array.isArray(row.values) ? row.values.map((value, valueIndex) => (
                      <td key={valueIndex}>{value}</td>
                    )) : <td>데이터 없음</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case 'process_flow':
        return (
          <div className="process-flow-container">
            <h4>{title}</h4>
            <div className="process-flow">
              {Array.isArray(currentData.steps) ? currentData.steps.map((step, index) => (
                <div key={index} className="process-step">
                  <div className="step-number">{index + 1}</div>
                  <div className="step-content">
                    <div className="step-title">{step.title || ''}</div>
                    <div className="step-description">{step.description || ''}</div>
                  </div>
                  {index < currentData.steps.length - 1 && (
                    <div className="step-arrow">→</div>
                  )}
                </div>
              )) : <div>프로세스 데이터가 없습니다.</div>}
            </div>
          </div>
        );

      case 'gauge_chart':
        const gaugeData = [{
          type: 'indicator',
          mode: 'gauge+number+delta',
          value: data.value,
          domain: { x: [0, 1], y: [0, 1] },
          title: { text: data.title },
          delta: { reference: data.target },
          gauge: {
            axis: { range: [null, data.max || 100] },
            bar: { color: data.color || '#1f77b4' },
            steps: [
              { range: [0, (data.max || 100) * 0.5], color: 'lightgray' },
              { range: [(data.max || 100) * 0.5, (data.max || 100) * 0.8], color: 'gray' }
            ],
            threshold: {
              line: { color: 'red', width: 4 },
              thickness: 0.75,
              value: data.target
            }
          }
        }];

        return (
          <Plot
            data={gaugeData}
            layout={{ width: 400, height: 300, margin: { t: 0, b: 0 } }}
            config={{ responsive: true }}
          />
        );

      default:
        return <div>지원되지 않는 시각화 타입: {type}</div>;
    }
  };

  return (
    <div className="advanced-visualization">
      <div className="viz-header">
        {title && <h3 className="viz-title">{title}</h3>}
        <div className="viz-controls">
          <VisualizationEditor
            data={currentData}
            onDataChange={handleDataChange}
            type={type}
          />
          <VisualizationCustomizer
            onThemeChange={setTheme}
            onSizeChange={setSize}
            currentTheme={theme}
            currentSize={size}
          />
        </div>
      </div>
      <div className="viz-content">
        {renderVisualization()}
      </div>
    </div>
  );
};

export default AdvancedVisualization;