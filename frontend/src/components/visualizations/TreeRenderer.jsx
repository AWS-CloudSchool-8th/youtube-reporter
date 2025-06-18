// frontend/src/components/visualizations/TreeRenderer.jsx
import React from 'react';

const TreeRenderer = ({ title, data }) => {
  if (!data || !data.root) {
    return (
      <div className="tree-error">
        <p>트리 데이터가 올바르지 않습니다</p>
      </div>
    );
  }

  const renderNode = (node, level = 0) => {
    if (typeof node === 'string') {
      return (
        <div style={{
          background: level === 0 ? 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' :
                     level === 1 ? 'linear-gradient(135deg, #ec4899 0%, #f093fb 100%)' :
                     'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          color: 'white',
          padding: '8px 15px',
          margin: '5px',
          borderRadius: level === 0 ? '25px' : '15px',
          fontSize: level === 0 ? '16px' : level === 1 ? '14px' : '12px',
          fontWeight: level === 0 ? '700' : '500',
          textAlign: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          minWidth: level === 0 ? '150px' : '100px'
        }}>
          {node}
        </div>
      );
    }

    return (
      <div style={{ textAlign: 'center', margin: '10px 0' }}>
        <div style={{
          background: level === 0 ? 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' :
                     level === 1 ? 'linear-gradient(135deg, #ec4899 0%, #f093fb 100%)' :
                     'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          color: 'white',
          padding: '10px 20px',
          margin: '5px auto',
          borderRadius: level === 0 ? '25px' : '15px',
          fontSize: level === 0 ? '16px' : level === 1 ? '14px' : '12px',
          fontWeight: level === 0 ? '700' : '500',
          display: 'inline-block',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
          minWidth: level === 0 ? '150px' : '100px'
        }}>
          {node.label}
        </div>

        {node.children && node.children.length > 0 && (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            flexWrap: 'wrap',
            gap: '10px',
            marginTop: '15px'
          }}>
            {node.children.map((child, index) => (
              <div key={index}>
                {renderNode(child, level + 1)}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="tree-container">
      <h4 style={{ textAlign: 'center', marginBottom: '20px', color: '#333' }}>
        {title}
      </h4>

      <div style={{
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        padding: '30px',
        borderRadius: '12px',
        overflow: 'auto'
      }}>
        {renderNode({ label: data.root, children: data.children }, 0)}
      </div>
    </div>
  );
};

export default TreeRenderer;