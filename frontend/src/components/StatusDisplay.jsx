// frontend/src/components/StatusDisplay.jsx
import React from 'react';

const StatusDisplay = ({ job }) => {
  if (!job) return null;

  const getStepInfo = (message, status) => {
    // 완료된 경우 모든 단계를 완료로 표시
    if (status === 'completed') return { step: 5, icon: '✅', phase: 'complete' };
    
    // 메시지에서 현재 단계 파악
    if (message.includes('자막')) return { step: 1, icon: '📝', phase: 'caption' };
    if (message.includes('분석') || message.includes('요약')) return { step: 2, icon: '🧠', phase: 'analysis' };
    if (message.includes('시각화')) return { step: 3, icon: '🎨', phase: 'visualization' };
    if (message.includes('리포트')) return { step: 4, icon: '📊', phase: 'report' };
    if (message.includes('완료')) return { step: 5, icon: '✅', phase: 'complete' };
    return { step: 0, icon: '⏳', phase: 'waiting' };
  };

  const currentStep = getStepInfo(job.message, job.status);

  const steps = [
    { id: 1, name: '자막 추출', icon: '📝', description: 'YouTube 영상의 자막을 추출합니다' },
    { id: 2, name: '내용 분석', icon: '🧠', description: '영상 내용을 깊이 있게 분석합니다' },
    { id: 3, name: '시각화 생성', icon: '🎨', description: '최적의 시각화를 자동 생성합니다' },
    { id: 4, name: '리포트 작성', icon: '📊', description: '종합적인 리포트를 생성합니다' },
    { id: 5, name: '완료', icon: '✅', description: '분석이 완료되었습니다' }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'queued': return '#fbbf24';
      case 'processing': return '#3b82f6';
      case 'completed': return '#10b981';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className="status-display">
      <div className="status-header">
        <h3>🔄 처리 상태</h3>
        <span
          className={`status-badge ${job.status}`}
          style={{ backgroundColor: getStatusColor(job.status) }}
        >
          {job.status.toUpperCase()}
        </span>
      </div>

      <div className="status-content">
        {/* 진행 단계 */}
        <div className="process-steps">
          {steps.map((step) => {
            const isCompleted = job.status === 'completed' ? step.id <= 5 : step.id < currentStep.step;
            const isActive = job.status === 'completed' ? false : step.id === currentStep.step;
            
            return (
              <div
                key={step.id}
                className={`process-step ${
                  isCompleted ? 'completed' : ''
                } ${isActive ? 'active' : ''}`}
              >
                <div className="step-circle">
                  <span className="step-icon">{step.icon}</span>
                </div>
                <div className="step-info">
                  <h4>{step.name}</h4>
                  <p>{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* 진행률 바 */}
        <div className="progress-container">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${job.progress || 0}%`,
                backgroundColor: getStatusColor(job.status)
              }}
            >
              <span className="progress-text">{job.progress || 0}%</span>
            </div>
          </div>
        </div>

        {/* 현재 메시지 */}
        <div className="status-message">
          <p>{job.status === 'completed' ? '🎉 분석이 완료되었습니다! 아래에서 결과를 확인하세요.' : job.message}</p>
        </div>

        {/* 추가 정보 */}
        <div className="status-details">
          {job.job_id && job.job_id !== 'starting...' && (
            <div className="detail-item">
              <span className="detail-label">작업 ID:</span>
              <span className="detail-value">{job.job_id}</span>
            </div>
          )}
          {job.created_at && (
            <div className="detail-item">
              <span className="detail-label">시작 시간:</span>
              <span className="detail-value">
                {new Date(job.created_at).toLocaleTimeString('ko-KR')}
              </span>
            </div>
          )}
          {job.status === 'processing' && (
            <div className="detail-item">
              <span className="detail-label">예상 시간:</span>
              <span className="detail-value">1-3분</span>
            </div>
          )}
        </div>

        {/* 에러 메시지 */}
        {job.error && (
          <div className="error-message">
            <h4>❌ 오류 발생</h4>
            <p>{job.error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatusDisplay;