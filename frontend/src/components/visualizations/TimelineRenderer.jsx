// frontend/src/components/visualizations/TimelineRenderer.jsx
import React from 'react';

const TimelineRenderer = ({ title, data }) => {
  if (!data || !data.events) {
    return (
      <div className="timeline-error">
        <p>타임라인 데이터가 올바르지 않습니다</p>
      </div>
    );
  }

  const { events = [] } = data;

  return (
    <div className="timeline-container">
      <h4 style={{ textAlign: 'center', marginBottom: '30px', color: '#333' }}>
        {title}
      </h4>

      <div className="timeline-content" style={{
        position: 'relative',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        padding: '20px',
        borderRadius: '12px'
      }}>
        {/* 중앙 라인 */}
        <div style={{
          position: 'absolute',
          left: '50%',
          top: '20px',
          bottom: '20px',
          width: '4px',
          background: 'linear-gradient(180deg, #6366f1 0%, #ec4899 100%)',
          transform: 'translateX(-50%)',
          borderRadius: '2px'
        }} />

        {events.map((event, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '40px',
              position: 'relative'
            }}
          >
            {/* 짝수는 왼쪽, 홀수는 오른쪽 */}
            {index % 2 === 0 ? (
              <>
                {/* 왼쪽 컨텐츠 */}
                <div style={{
                  flex: '1',
                  textAlign: 'right',
                  paddingRight: '30px'
                }}>
                  <div style={{
                    background: 'white',
                    padding: '15px',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    border: '2px solid #6366f1'
                  }}>
                    <div style={{
                      background: '#6366f1',
                      color: 'white',
                      padding: '5px 10px',
                      borderRadius: '15px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      display: 'inline-block',
                      marginBottom: '8px'
                    }}>
                      {event.time}
                    </div>
                    <h5 style={{ margin: '0 0 8px 0', color: '#333' }}>
                      {event.title}
                    </h5>
                    <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
                      {event.description}
                    </p>
                  </div>
                </div>

                {/* 중앙 점 */}
                <div style={{
                  width: '16px',
                  height: '16px',
                  background: '#6366f1',
                  borderRadius: '50%',
                  border: '4px solid white',
                  boxShadow: '0 2px 8px rgba(99, 102, 241, 0.3)',
                  zIndex: 10,
                  position: 'relative'
                }} />

                {/* 오른쪽 빈 공간 */}
                <div style={{ flex: '1' }} />
              </>
            ) : (
              <>
                {/* 왼쪽 빈 공간 */}
                <div style={{ flex: '1' }} />

                {/* 중앙 점 */}
                <div style={{
                  width: '16px',
                  height: '16px',
                  background: '#ec4899',
                  borderRadius: '50%',
                  border: '4px solid white',
                  boxShadow: '0 2px 8px rgba(236, 72, 153, 0.3)',
                  zIndex: 10,
                  position: 'relative'
                }} />

                {/* 오른쪽 컨텐츠 */}
                <div style={{
                  flex: '1',
                  textAlign: 'left',
                  paddingLeft: '30px'
                }}>
                  <div style={{
                    background: 'white',
                    padding: '15px',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    border: '2px solid #ec4899'
                  }}>
                    <div style={{
                      background: '#ec4899',
                      color: 'white',
                      padding: '5px 10px',
                      borderRadius: '15px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      display: 'inline-block',
                      marginBottom: '8px'
                    }}>
                      {event.time}
                    </div>
                    <h5 style={{ margin: '0 0 8px 0', color: '#333' }}>
                      {event.title}
                    </h5>
                    <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
                      {event.description}
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelineRenderer;