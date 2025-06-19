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

  const addDataPoint = () => {
    if (editData.labels && editData.datasets) {
      const newEditData = { ...editData };
      newEditData.labels.push(`항목${newEditData.labels.length + 1}`);
      newEditData.datasets.forEach(dataset => {
        dataset.data.push(Math.floor(Math.random() * 100));
      });
      setEditData(newEditData);
    }
  };

  const removeDataPoint = (index) => {
    if (editData.labels && editData.datasets) {
      const newEditData = { ...editData };
      newEditData.labels.splice(index, 1);
      newEditData.datasets.forEach(dataset => {
        dataset.data.splice(index, 1);
      });
      setEditData(newEditData);
    }
  };

  const updateLabel = (index, value) => {
    const newEditData = { ...editData };
    newEditData.labels[index] = value;
    setEditData(newEditData);
  };

  const updateValue = (datasetIndex, valueIndex, value) => {
    const newEditData = { ...editData };
    newEditData.datasets[datasetIndex].data[valueIndex] = parseFloat(value) || 0;
    setEditData(newEditData);
  };

  if (!isEditing) {
    return (
      <button 
        className="edit-btn"
        onClick={() => setIsEditing(true)}
        title="데이터 편집"
      >
        ✏️ 편집
      </button>
    );
  }

  return (
    <div className="visualization-editor">
      <div className="editor-header">
        <h4>데이터 편집</h4>
        <div className="editor-actions">
          <button onClick={handleSave} className="save-btn">💾 저장</button>
          <button onClick={handleCancel} className="cancel-btn">❌ 취소</button>
        </div>
      </div>

      <div className="editor-content">
        {editData.labels && editData.datasets && (
          <div className="data-table">
            <table>
              <thead>
                <tr>
                  <th>라벨</th>
                  {editData.datasets.map((dataset, i) => (
                    <th key={i}>{dataset.label || `데이터${i + 1}`}</th>
                  ))}
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {editData.labels.map((label, index) => (
                  <tr key={index}>
                    <td>
                      <input
                        type="text"
                        value={label}
                        onChange={(e) => updateLabel(index, e.target.value)}
                      />
                    </td>
                    {editData.datasets.map((dataset, datasetIndex) => (
                      <td key={datasetIndex}>
                        <input
                          type="number"
                          value={dataset.data[index] || 0}
                          onChange={(e) => updateValue(datasetIndex, index, e.target.value)}
                        />
                      </td>
                    ))}
                    <td>
                      <button 
                        onClick={() => removeDataPoint(index)}
                        className="remove-btn"
                        title="삭제"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button onClick={addDataPoint} className="add-btn">
              ➕ 데이터 추가
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default VisualizationEditor;