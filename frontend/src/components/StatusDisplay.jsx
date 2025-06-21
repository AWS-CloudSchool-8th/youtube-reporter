import React from 'react';

const StatusDisplay = ({ job }) => {
  if (!job) return null;

  const getStepInfo = (status, progress) => {
    // 실제 백엔드 단계와 동기화
    if (status === 'queued') return { text: '대기 중...', icon: '⏳', step: 0 };
    if (status === 'processing') {
      if (progress <= 25) return { text: '자막 추출 중...', icon: '📝', step: 1 };
      if (progress <= 50) return { text: 'AI 요약 생성 중...', icon: '🤖', step: 2 };
      if (progress <= 75) return { text: '시각화 데이터 생성 중...', icon: '📊', step: 3 };
      return { text: '최종 결과 생성 중...', icon: '🎯', step: 4 };
    }
    if (status === 'completed') return { text: '완료!', icon: '✅', step: 5 };
    if (status === 'failed') return { text: '실패', icon: '❌', step: 0 };
    return { text: '알 수 없음', icon: '❓', step: 0 };
  };

  const currentStep = getStepInfo(job.status, job.progress || 0);

  return (
    <div className="status-display">
      <h3>📊 처리 상태</h3>
      
      <div className="status-card">
        <div className="status-info">
          <span className={`status-badge ${job.status}`}>
            {currentStep.icon} {currentStep.text}
          </span>
        </div>

        <div className="progress-container">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${job.progress || 0}%` }}
            />
          </div>
          <span className="progress-text">{job.progress || 0}%</span>
        </div>

        <div className="job-details">
          <div className="job-id">
            <strong>작업 ID:</strong> {job.job_id}
          </div>
          {job.created_at && (
            <div className="job-time">
              <strong>시작:</strong> {new Date(job.created_at).toLocaleTimeString()}
            </div>
          )}
        </div>

        {job.error && (
          <div className="error-details">
            <strong>오류:</strong> {job.error}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatusDisplay;