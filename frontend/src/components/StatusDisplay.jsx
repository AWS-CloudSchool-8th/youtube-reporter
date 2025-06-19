// frontend/src/components/StatusDisplay.jsx
import React from 'react';

const StatusDisplay = ({ job }) => {
  if (!job) return null;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'queued': return '🔄';
      case 'processing': return '⚙️';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '❓';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'queued': return '대기';
      case 'processing': return '처리 중';
      case 'completed': return '완료';
      case 'failed': return '실패';
      default: return '알 수 없음';
    }
  };

  return (
    <div className="status-display">
      <h3>📊 처리 상태</h3>

      <div className="status-card">
        <div className="status-info">
          <span className={`status-badge ${job.status}`}>
            {getStatusIcon(job.status)} {getStatusText(job.status)}
          </span>
          <span className="status-message">{job.message}</span>
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
              <strong>시작 시간:</strong> {new Date(job.created_at).toLocaleString()}
            </div>
          )}
          {job.completed_at && (
            <div className="job-time">
              <strong>완료 시간:</strong> {new Date(job.completed_at).toLocaleString()}
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