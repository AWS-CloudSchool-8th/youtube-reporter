// frontend/src/components/visualizations/ComparisonRenderer.jsx
import React from 'react';

const ComparisonRenderer = ({ title, data }) => {
  if (!data || !data.items || !data.criteria) {
    return (
      <div className="comparison-error">
        <p>비교표 데이터가 올바르지 않습니다</p>
      </div>
    );
  }

  const { items = [], criteria = [], values = [] } = data;

  return (
    <div className="comparison-container">
      <h4 style={{ textAlign: 'center', marginBottom: '20px', color: '#333' }}>
        {title}
      </h4>

      <div style={{
        background: 'white',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '14px'
        }}>
          <thead>
            <tr style={{ background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' }}>
              <th style={{
                padding: '15px',
                color: 'white',
                fontWeight: '600',
                textAlign: 'left',
                borderRight: '1px solid rgba(255,255,255,0.2)'
              }}>
                항목 / 기준
              </th>
              {criteria.map((criterion, index) => (
                <th key={index} style={{
                  padding: '15px',
                  color: 'white',
                  fontWeight: '600',
                  textAlign: 'center',
                  borderRight: index < criteria.length - 1 ? '1px solid rgba(255,255,255,0.2)' : 'none'
                }}>
                  {criterion}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((item, rowIndex) => (
              <tr key={rowIndex} style={{
                background: rowIndex % 2 === 0 ? '#f8fafc' : 'white',
                borderBottom: '1px solid #e2e8f0'
              }}>
                <td style={{
                  padding: '15px',
                  fontWeight: '600',
                  color: '#333',
                  background: 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
                  borderRight: '2px solid #6366f1'
                }}>
                  {item}
                </td>
                {criteria.map((_, colIndex) => (
                  <td key={colIndex} style={{
                    padding: '15px',
                    textAlign: 'center',
                    color: '#555',
                    borderRight: colIndex < criteria.length - 1 ? '1px solid #e2e8f0' : 'none'
                  }}>
                    {values[rowIndex] && values[rowIndex][colIndex] ? (
                      <span style={{
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '500'
                      }}>
                        {values[rowIndex][colIndex]}
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ComparisonRenderer;