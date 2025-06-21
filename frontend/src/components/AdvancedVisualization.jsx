import React, { useState } from 'react';
import { ResponsiveBar } from '@nivo/bar';
import { ResponsiveLine } from '@nivo/line';
import { ResponsivePie } from '@nivo/pie';
import { ResponsiveHeatMap } from '@nivo/heatmap';
import { ResponsiveNetwork } from '@nivo/network';

import './AdvancedVisualization.css';

const AdvancedVisualization = ({ type, data, title }) => {
  const [currentData, setCurrentData] = useState(data);
  const [theme, setTheme] = useState('default');

  const [editMode, setEditMode] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  if (!currentData) return <div>데이터가 없습니다.</div>;

  const themes = {
    default: {
      background: '#ffffff',
      colors: ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#764ba2', '#fbbf24', '#06b6d4'],
      textColor: '#1f2937',
      gridColor: '#e5e7eb'
    },
    professional: {
      background: '#f8fafc',
      colors: ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'],
      textColor: '#1e293b',
      gridColor: '#cbd5e1'
    },
    dark: {
      background: '#1a1a1a',
      colors: ['#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#84cc16', '#f97316'],
      textColor: '#f9fafb',
      gridColor: '#374151'
    },
    neon: {
      background: '#0a0a0a',
      colors: ['#00ffff', '#ff00ff', '#ffff00', '#00ff00', '#ff0080', '#8000ff', '#ff4000', '#0080ff'],
      textColor: '#ffffff',
      gridColor: '#333333'
    },
    pastel: {
      background: '#fefefe',
      colors: ['#a8dadc', '#f1faee', '#e63946', '#f77f00', '#fcbf49', '#457b9d', '#e9c46a', '#2a9d8f'],
      textColor: '#2d3436',
      gridColor: '#e2e8f0'
    }
  };

  const currentTheme = themes[theme];

  const convertToNivoData = (chartData) => {
    if (!chartData.labels || !chartData.datasets) return [];
    
    return chartData.labels.map((label, index) => {
      const item = { id: label };
      chartData.datasets.forEach((dataset, datasetIndex) => {
        item[dataset.label || `data${datasetIndex}`] = dataset.data[index] || 0;
      });
      return item;
    });
  };

  const convertToPieData = (chartData) => {
    if (!chartData.labels || !chartData.datasets?.[0]) return [];
    
    return chartData.labels.map((label, index) => ({
      id: label,
      label: label,
      value: chartData.datasets[0].data[index] || 0
    }));
  };

  const handleDataEdit = (newValue, itemId, field) => {
    if (!currentData) return;
    
    const updatedData = { ...currentData };
    
    if (type === 'bar_chart' || type === 'line_chart') {
      if (!updatedData.labels || !updatedData.datasets?.[0]) return;
      
      const labelIndex = updatedData.labels.indexOf(itemId);
      if (labelIndex !== -1 && field === 'value') {
        updatedData.datasets[0].data[labelIndex] = parseFloat(newValue) || 0;
      } else if (field === 'label') {
        updatedData.labels[labelIndex] = newValue;
      }
    } else if (type === 'timeline') {
      if (updatedData.events && updatedData.events[itemId]) {
        updatedData.events[itemId][field] = newValue;
      }
    } else if (type === 'process_flow') {
      if (updatedData.steps && updatedData.steps[itemId]) {
        updatedData.steps[itemId][field] = newValue;
      }
    } else if (type === 'comparison_table') {
      if (field === 'header' && itemId.startsWith('col-')) {
        const colIndex = parseInt(itemId.split('-')[1]);
        if (updatedData.columns && updatedData.columns[colIndex]) {
          updatedData.columns[colIndex] = newValue;
        }
      } else if (field === 'name' && itemId.startsWith('row-')) {
        const rowIndex = parseInt(itemId.split('-')[1]);
        if (updatedData.rows && updatedData.rows[rowIndex]) {
          updatedData.rows[rowIndex].name = newValue;
        }
      } else if (field === 'value' && itemId.startsWith('cell-')) {
        const [, rowIndex, colIndex] = itemId.split('-').map(Number);
        if (updatedData.rows && updatedData.rows[rowIndex] && updatedData.rows[rowIndex].values) {
          updatedData.rows[rowIndex].values[colIndex] = newValue;
        }
      }
    }
    
    setCurrentData(updatedData);
  };

  const addDataPoint = () => {
    const updatedData = { ...currentData };
    
    if (type === 'bar_chart' || type === 'line_chart' || type === 'pie_chart') {
      if (!updatedData.labels || !updatedData.datasets) return;
      
      const newLabel = `항목${updatedData.labels.length + 1}`;
      updatedData.labels.push(newLabel);
      updatedData.datasets.forEach(dataset => {
        if (dataset.data) {
          dataset.data.push(Math.floor(Math.random() * 100));
        }
      });
    } else if (type === 'heatmap') {
      if (!updatedData.labels || !updatedData.datasets) return;
      const newLabel = `항목${updatedData.labels.length + 1}`;
      updatedData.labels.push(newLabel);
      updatedData.datasets.forEach(dataset => {
        if (dataset.data) {
          dataset.data.push(Math.floor(Math.random() * 100));
        }
      });
    } else if (type === 'network') {
      if (!updatedData.nodes) updatedData.nodes = [];
      if (!updatedData.links) updatedData.links = [];
      const newNodeId = `node-${updatedData.nodes.length + 1}`;
      updatedData.nodes.push({
        id: newNodeId,
        text: `노드 ${updatedData.nodes.length + 1}`,
        level: 1
      });
    } else if (type === 'process_flow') {
      if (!updatedData.steps) updatedData.steps = [];
      updatedData.steps.push({
        title: `단계 ${updatedData.steps.length + 1}`,
        description: '새로운 단계 설명'
      });
    } else if (type === 'timeline') {
      if (!updatedData.events) updatedData.events = [];
      updatedData.events.push({
        date: '2024-01',
        title: `이벤트 ${updatedData.events.length + 1}`,
        description: '새로운 이벤트 설명'
      });
    } else if (type === 'comparison_table') {
      if (!updatedData.rows) updatedData.rows = [];
      if (!updatedData.columns) updatedData.columns = ['열1', '열2'];
      updatedData.rows.push({
        name: `항목${updatedData.rows.length + 1}`,
        values: ['값1', '값2']
      });
    }
    
    setCurrentData(updatedData);
  };

  const removeDataPoint = (itemId) => {
    if (!currentData?.labels || !currentData?.datasets) return;
    
    const updatedData = { ...currentData };
    const labelIndex = updatedData.labels.indexOf(itemId);
    
    if (labelIndex !== -1) {
      updatedData.labels.splice(labelIndex, 1);
      updatedData.datasets.forEach(dataset => {
        if (dataset.data) {
          dataset.data.splice(labelIndex, 1);
        }
      });
    }
    
    setCurrentData(updatedData);
  };

  const getContainerClass = () => {
    const dataCount = currentData?.labels?.length || currentData?.steps?.length || currentData?.events?.length || currentData?.rows?.length || 0;
    
    if (dataCount > 15) return 'extra-large-dataset';
    if (dataCount > 10) return 'large-dataset';
    return '';
  };

  const renderVisualization = () => {
    switch (type) {
      case 'bar_chart':
        const barData = convertToNivoData(currentData);
        const keys = currentData.datasets?.map(d => d.label || 'data') || ['data'];
        
        return (
          <div className="chart-wrapper" style={{ background: currentTheme.background }}>
            <ResponsiveBar
              data={barData}
              keys={keys}
              indexBy="id"
              margin={{ top: 50, right: 130, bottom: 50, left: 60 }}
              padding={0.3}
              valueScale={{ type: 'linear' }}
              colors={currentTheme.colors}
              theme={{
                background: currentTheme.background,
                textColor: currentTheme.textColor,
                grid: { line: { stroke: currentTheme.gridColor } }
              }}
              animate={true}
              motionStiffness={90}
              motionDamping={15}
              onClick={(data) => {
                if (editMode) {
                  const value = data.value || data.data?.[data.id] || 0;
                  const newValue = prompt('새 값 입력:', value);
                  if (newValue !== null) handleDataEdit(newValue, data.id || data.indexValue, 'value');
                }
              }}
              legends={[
                {
                  dataFrom: 'keys',
                  anchor: 'bottom-right',
                  direction: 'column',
                  justify: false,
                  translateX: 120,
                  translateY: 0,
                  itemsSpacing: 2,
                  itemWidth: 100,
                  itemHeight: 20,
                  itemDirection: 'left-to-right',
                  itemOpacity: 0.85,
                  symbolSize: 20,
                  effects: [
                    {
                      on: 'hover',
                      style: {
                        itemOpacity: 1
                      }
                    }
                  ]
                }
              ]}
            />
          </div>
        );

      case 'line_chart':
        const lineData = currentData.datasets?.map((dataset, index) => ({
          id: dataset.label || `Line ${index + 1}`,
          color: currentTheme.colors[index % currentTheme.colors.length],
          data: currentData.labels?.map((label, i) => ({
            x: label,
            y: dataset.data[i] || 0
          })) || []
        })) || [];

        return (
          <div className="chart-wrapper" style={{ background: currentTheme.background }}>
            <ResponsiveLine
              data={lineData}
              margin={{ top: 50, right: 110, bottom: 50, left: 60 }}
              xScale={{ type: 'point' }}
              yScale={{ type: 'linear', min: 'auto', max: 'auto', stacked: false }}
              curve="cardinal"
              axisTop={null}
              axisRight={null}
              colors={currentTheme.colors}
              theme={{
                background: currentTheme.background,
                textColor: currentTheme.textColor,
                grid: { line: { stroke: currentTheme.gridColor } }
              }}
              pointSize={10}
              pointColor={{ theme: 'background' }}
              pointBorderWidth={2}
              pointBorderColor={{ from: 'serieColor' }}
              pointLabelYOffset={-12}
              useMesh={true}
              animate={true}
              motionStiffness={120}
              motionDamping={50}
              onClick={(point) => {
                if (editMode) {
                  const value = point.data.y;
                  const newValue = prompt('새 값 입력:', value);
                  if (newValue !== null) handleDataEdit(newValue, point.data.x, 'value');
                }
              }}
              legends={[
                {
                  anchor: 'bottom-right',
                  direction: 'column',
                  justify: false,
                  translateX: 100,
                  translateY: 0,
                  itemsSpacing: 0,
                  itemDirection: 'left-to-right',
                  itemWidth: 80,
                  itemHeight: 20,
                  itemOpacity: 0.75,
                  symbolSize: 12,
                  symbolShape: 'circle',
                  symbolBorderColor: 'rgba(0, 0, 0, .5)',
                  effects: [
                    {
                      on: 'hover',
                      style: {
                        itemBackground: 'rgba(0, 0, 0, .03)',
                        itemOpacity: 1
                      }
                    }
                  ]
                }
              ]}
            />
          </div>
        );

      case 'pie_chart':
        const pieData = convertToPieData(currentData);
        
        return (
          <div className="chart-wrapper" style={{ background: currentTheme.background }}>
            <ResponsivePie
              data={pieData}
              margin={{ top: 40, right: 80, bottom: 80, left: 80 }}
              innerRadius={0.5}
              padAngle={0.7}
              cornerRadius={3}
              colors={currentTheme.colors}
              theme={{
                background: currentTheme.background,
                textColor: currentTheme.textColor
              }}
              borderWidth={1}
              borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
              radialLabelsSkipAngle={10}
              radialLabelsTextColor={currentTheme.textColor}
              radialLabelsLinkColor={{ from: 'color' }}
              sliceLabelsSkipAngle={10}
              sliceLabelsTextColor="#333333"
              animate={true}
              motionStiffness={90}
              motionDamping={15}
              onClick={(data) => {
                if (editMode) {
                  const value = data.value;
                  const newValue = prompt('새 값 입력:', value);
                  if (newValue !== null) handleDataEdit(newValue, data.id, 'value');
                }
              }}
              legends={[
                {
                  anchor: 'bottom',
                  direction: 'row',
                  justify: false,
                  translateX: 0,
                  translateY: 56,
                  itemsSpacing: 0,
                  itemWidth: 100,
                  itemHeight: 18,
                  itemTextColor: currentTheme.textColor,
                  itemDirection: 'left-to-right',
                  itemOpacity: 1,
                  symbolSize: 18,
                  symbolShape: 'circle',
                  effects: [
                    {
                      on: 'hover',
                      style: {
                        itemTextColor: currentTheme.colors[0]
                      }
                    }
                  ]
                }
              ]}
            />
          </div>
        );

      case 'heatmap':
        const heatmapData = currentData.labels?.map((label, index) => ({
          id: label,
          data: currentData.datasets?.map((dataset, datasetIndex) => ({
            x: dataset.label || `Series ${datasetIndex + 1}`,
            y: dataset.data[index] || 0
          })) || []
        })) || [];

        return (
          <div className="chart-wrapper" style={{ background: currentTheme.background }}>
            <ResponsiveHeatMap
              data={heatmapData}
              margin={{ top: 60, right: 90, bottom: 60, left: 90 }}
              valueFormat=">-.2s"
              axisTop={{
                tickSize: 5,
                tickPadding: 5,
                tickRotation: -90,
                legend: '',
                legendOffset: 46
              }}
              axisRight={{
                tickSize: 5,
                tickPadding: 5,
                tickRotation: 0,
                legend: 'country',
                legendPosition: 'middle',
                legendOffset: 70
              }}
              axisLeft={{
                tickSize: 5,
                tickPadding: 5,
                tickRotation: 0,
                legend: 'country',
                legendPosition: 'middle',
                legendOffset: -72
              }}
              colors={{
                type: 'diverging',
                scheme: 'red_yellow_blue',
                divergeAt: 0.5,
                minValue: 0,
                maxValue: 100
              }}
              emptyColor="#555555"
              theme={{
                background: currentTheme.background,
                textColor: currentTheme.textColor
              }}
              animate={true}
              motionStiffness={80}
              motionDamping={9}
              onClick={(data) => editMode && setEditingItem(data)}
            />
          </div>
        );

      case 'network':
        const networkData = {
          nodes: currentData.nodes?.map((node, index) => ({
            id: node.id || node.text || `node-${index}`,
            height: 1,
            size: 20 + (node.level || 0) * 10,
            color: currentTheme.colors[index % currentTheme.colors.length]
          })) || [],
          links: currentData.links?.map(link => ({
            source: link.source,
            target: link.target,
            distance: 80
          })) || []
        };

        return (
          <div className="chart-wrapper" style={{ background: currentTheme.background }}>
            <ResponsiveNetwork
              data={networkData}
              margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
              linkDistance={function(e){return e.distance}}
              centeringStrength={0.3}
              repulsivity={6}
              nodeSize={function(n){return n.size}}
              activeNodeSize={function(n){return 1.5*n.size}}
              nodeColor={function(n){return n.color}}
              nodeBorderWidth={1}
              nodeBorderColor={{ from: 'color', modifiers: [['darker', 0.8]] }}
              linkThickness={function(n){return 2+2*n.target.data.height}}
              linkBlendMode="multiply"
              motionStiffness={160}
              motionDamping={12}
              animate={true}
              onClick={(node) => editMode && setEditingItem(node)}
            />
          </div>
        );

      case 'comparison_table':
        const tableClass = `comparison-table ${
          currentData.columns?.length > 5 ? 'many-columns' : ''
        } ${
          currentData.rows?.length > 10 ? 'many-rows' : ''
        }`;
        
        return (
          <div className="comparison-table-container">
            <table className={tableClass}>
              <thead>
                <tr>
                  <th>항목</th>
                  {currentData.columns?.map((col, index) => (
                    <th key={index} style={{cursor: editMode ? 'pointer' : 'default'}}>
                      {editMode ? (
                        <input className="inline-edit-cell" defaultValue={col} onBlur={(e) => handleDataEdit(e.target.value, `col-${index}`, 'header')} />
                      ) : col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {currentData.rows?.map((row, index) => (
                  <tr key={index}>
                    <td className="row-header" style={{cursor: editMode ? 'pointer' : 'default'}}>
                      {editMode ? (
                        <input className="inline-edit-cell" defaultValue={row.name} onBlur={(e) => handleDataEdit(e.target.value, `row-${index}`, 'name')} />
                      ) : row.name}
                    </td>
                    {Array.isArray(row.values) ? row.values.map((value, valueIndex) => (
                      <td key={valueIndex} style={{cursor: editMode ? 'pointer' : 'default'}}>
                        {editMode ? (
                          <input className="inline-edit-cell" defaultValue={value} onBlur={(e) => handleDataEdit(e.target.value, `cell-${index}-${valueIndex}`, 'value')} />
                        ) : value}
                      </td>
                    )) : <td>-</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case 'process_flow':
        return (
          <div className="process-flow-container">
            <div className={`process-flow ${currentData.steps?.length > 6 ? 'many-steps' : ''}`}>
              {currentData.steps?.map((step, index) => (
                <div key={index} className="process-step" style={{cursor: editMode ? 'pointer' : 'default'}}>
                  <div className="step-number">{index + 1}</div>
                  <div className="step-content">
                    {editMode ? (
                      <>
                        <input 
                          className="inline-edit-title"
                          defaultValue={step.title}
                          onBlur={(e) => handleDataEdit(e.target.value, index, 'title')}
                        />
                        <textarea 
                          className="inline-edit-desc"
                          defaultValue={step.description}
                          onBlur={(e) => handleDataEdit(e.target.value, index, 'description')}
                        />
                      </>
                    ) : (
                      <>
                        <h5>{step.title}</h5>
                        <p>{step.description}</p>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'timeline':
        return (
          <div className="timeline-container">
            <div className={`timeline ${currentData.events?.length > 8 ? 'many-events' : ''}`}>
              {currentData.events?.map((event, index) => (
                <div key={index} className="timeline-item" style={{cursor: editMode ? 'pointer' : 'default'}}>
                  <div className="timeline-marker"></div>
                  <div className="timeline-content">
                    {editMode ? (
                      <>
                        <input 
                          className="inline-edit-date"
                          defaultValue={event.date}
                          onBlur={(e) => handleDataEdit(e.target.value, index, 'date')}
                        />
                        <input 
                          className="inline-edit-title"
                          defaultValue={event.title}
                          onBlur={(e) => handleDataEdit(e.target.value, index, 'title')}
                        />
                        <textarea 
                          className="inline-edit-desc"
                          defaultValue={event.description}
                          onBlur={(e) => handleDataEdit(e.target.value, index, 'description')}
                        />
                      </>
                    ) : (
                      <>
                        <div className="timeline-date">{event.date}</div>
                        <div className="timeline-title">{event.title}</div>
                        <div className="timeline-description">{event.description}</div>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return <div>지원하지 않는 시각화 타입: {type}</div>;
    }
  };

  return (
    <div className={`advanced-visualization ${getContainerClass()}`}>
      <div className="viz-controls">
        <div className="control-group">
          <label>테마:</label>
          <select value={theme} onChange={(e) => setTheme(e.target.value)}>
            <option value="default">기본</option>
            <option value="professional">전문가</option>
            <option value="dark">다크</option>
            <option value="neon">네온</option>
            <option value="pastel">파스텔</option>
          </select>
        </div>
        

        
        <div className="control-group">
          <button 
            className={`edit-btn ${editMode ? 'active' : ''}`}
            onClick={() => setEditMode(!editMode)}
          >
            {editMode ? '✅ 편집완료' : '✏️ 편집모드'}
          </button>
        </div>

        {editMode && (
          <div className="control-group">
            <button onClick={addDataPoint} className="add-btn">
              ➕ {type === 'process_flow' ? '단계 추가' : type === 'timeline' ? '이벤트 추가' : type === 'comparison_table' ? '행 추가' : '데이터 추가'}
            </button>
          </div>
        )}
      </div>

      <div className="viz-content">
        {renderVisualization()}
      </div>


    </div>
  );
};

export default AdvancedVisualization;