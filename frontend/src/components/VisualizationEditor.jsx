// frontend/src/components/VisualizationEditor.jsx
import React, { useState } from 'react';

const VisualizationEditor = ({ data, onDataChange, type }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState(data);

  const handleSave = () => {
    onDataChange(editData);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditData(data);
    setIsEditing(false);
  };

  const updateChartData = (labelIndex, value) => {
    const newData = { ...editData };
    if (newData.datasets && newData.datasets[0]) {
      newData.datasets[0].data[labelIndex] = parseFloat(value) || 0;
    }
    setEditData(newData);
  };

  const updateLabel = (index, newLabel) => {
    const newData = { ...editData };
    if (newData.labels) {
      newData.labels[index] = newLabel;
    }
    setEditData(newData);
  };

  const addDataPoint = () => {
    const newData = { ...editData };
    if (newData.labels && newData.datasets && newData.datasets[0]) {
      newData.labels.push(`새 항목 ${newData.labels.length + 1}`);
      newData.datasets[0].data.push(0);
    }
    setEditData(newData);
  };

  const removeDataPoint = (index) => {
    const newData = { ...editData };
    if (newData.labels && newData.datasets && newData.datasets[0]) {
      newData.labels.splice(index, 1);
      newData.datasets[0].data.splice(index, 1);
    }
    setEditData(newData);
  };

  const updateProcessStep = (index, field, value) => {
    const newData = { ...editData };
    if (newData.steps && newData.steps[index]) {
      newData.steps[index][field] = value;
    }
    setEditData(newData);
  };

  const addProcessStep = () => {
    const newData = { ...editData };
    if (newData.steps) {
      newData.steps.push({
        title: `새 단계 ${newData.steps.length + 1}`,
        description: '설명을 입력하세요'
      });
    }
    setEditData(newData);
  };

  const updateTimelineEvent = (index, field, value) => {
    const newData = { ...editData };
    if (newData.events && newData.events[index]) {
      newData.events[index][field] = value;
    }
    setEditData(newData);
  };

  const addTimelineEvent = () => {
    const newData = { ...editData };
    if (newData.events) {
      newData.events.push({
        date: '2024',
        title: '새 이벤트',
        description: '설명을 입력하세요'
      });
    }
    setEditData(newData);
  };

  const renderChartEditor = () => (
    <div className="chart-editor">
      <h4>데이터 편집</h4>
      {editData.labels?.map((label, index) => (
        <div key={index} className="data-row">
          <input
            type="text"
            value={label}
            onChange={(e) => updateLabel(index, e.target.value)}
            className="label-input"
            placeholder="항목명"
          />
          <input
            type="number"
            value={editData.datasets?.[0]?.data?.[index] || 0}
            onChange={(e) => updateChartData(index, e.target.value)}
            className="value-input"
            placeholder="값"
          />
          <button 
            onClick={() => removeDataPoint(index)}
            className="remove-btn"
          >
            ✕
          </button>
        </div>
      ))}
      <button onClick={addDataPoint} className="add-btn">
        + 데이터 추가
      </button>
    </div>
  );

  const renderProcessEditor = () => (
    <div className="process-editor">
      <h4>단계 편집</h4>
      {editData.steps?.map((step, index) => (
        <div key={index} className="step-editor">
          <input
            type="text"
            value={step.title}
            onChange={(e) => updateProcessStep(index, 'title', e.target.value)}
            className="step-title-input"
            placeholder="단계 제목"
          />
          <textarea
            value={step.description}
            onChange={(e) => updateProcessStep(index, 'description', e.target.value)}
            className="step-desc-input"
            placeholder="단계 설명"
            rows="2"
          />
        </div>
      ))}
      <button onClick={addProcessStep} className="add-btn">
        + 단계 추가
      </button>
    </div>
  );

  const renderTimelineEditor = () => (
    <div className="timeline-editor">
      <h4>이벤트 편집</h4>
      {editData.events?.map((event, index) => (
        <div key={index} className="event-editor">
          <input
            type="text"
            value={event.date}
            onChange={(e) => updateTimelineEvent(index, 'date', e.target.value)}
            className="event-date-input"
            placeholder="날짜"
          />
          <input
            type="text"
            value={event.title}
            onChange={(e) => updateTimelineEvent(index, 'title', e.target.value)}
            className="event-title-input"
            placeholder="이벤트 제목"
          />
          <textarea
            value={event.description}
            onChange={(e) => updateTimelineEvent(index, 'description', e.target.value)}
            className="event-desc-input"
            placeholder="이벤트 설명"
            rows="2"
          />
        </div>
      ))}
      <button onClick={addTimelineEvent} className="add-btn">
        + 이벤트 추가
      </button>
    </div>
  );

  const renderEditor = () => {
    if (type === 'bar_chart' || type === 'line_chart' || type === 'pie_chart') {
      return renderChartEditor();
    } else if (type === 'process_flow') {
      return renderProcessEditor();
    } else if (type === 'timeline') {
      return renderTimelineEditor();
    }
    return <div>이 시각화 타입은 편집을 지원하지 않습니다.</div>;
  };

  return (
    <div className="viz-editor">
      <button 
        className="edit-toggle"
        onClick={() => setIsEditing(!isEditing)}
      >
        ✏️ 편집
      </button>

      {isEditing && (
        <div className="editor-panel">
          {renderEditor()}
          <div className="editor-actions">
            <button onClick={handleSave} className="save-btn">
              저장
            </button>
            <button onClick={handleCancel} className="cancel-btn">
              취소
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VisualizationEditor;