// frontend/src/components/AdvancedVisualization.jsx
import React from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  ScatterChart, Scatter, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import Plot from 'react-plotly.js';

const AdvancedVisualization = ({ type, data, title }) => {
  if (!data) return <div>데이터가 없습니다.</div>;

  const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

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
        const barData = convertToRechartsData(data);
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {data.datasets?.map((dataset, index) => (
                <Bar 
                  key={index}
                  dataKey={dataset.label || `데이터${index + 1}`}
                  fill={colors[index % colors.length]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line_chart':
        const lineData = convertToRechartsData(data);
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={lineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {data.datasets?.map((dataset, index) => (
                <Line 
                  key={index}
                  type="monotone"
                  dataKey={dataset.label || `데이터${index + 1}`}
                  stroke={colors[index % colors.length]}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie_chart':
        const pieData = data.labels?.map((label, index) => ({
          name: label,
          value: data.datasets?.[0]?.data?.[index] || 0
        })) || [];
        
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
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
              {Array.isArray(data.events) ? data.events.map((event, index) => (
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
              {Array.isArray(data.steps) ? data.steps.map((step, index) => (
                <div key={index} className="process-step">
                  <div className="step-number">{index + 1}</div>
                  <div className="step-content">
                    <div className="step-title">{step.title || ''}</div>
                    <div className="step-description">{step.description || ''}</div>
                  </div>
                  {index < data.steps.length - 1 && (
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
      {title && <h3 className="viz-title">{title}</h3>}
      <div className="viz-content">
        {renderVisualization()}
      </div>
    </div>
  );
};

export default AdvancedVisualization;