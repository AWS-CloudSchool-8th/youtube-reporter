// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import './App.css';

// 컴포넌트들
const VideoProcessor = () => {
  const [url, setUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [jobs, setJobs] = useState([]);

  const API_BASE = 'http://localhost:8000';

  // YouTube URL 유효성 검사
  const isValidYouTubeUrl = (url) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/;
    return youtubeRegex.test(url);
  };

  // 영상 처리 시작
  const processVideo = async () => {
    if (!url.trim()) {
      setError('YouTube URL을 입력해주세요.');
      return;
    }

    if (!isValidYouTubeUrl(url)) {
      setError('올바른 YouTube URL을 입력해주세요.');
      return;
    }

    try {
      setIsProcessing(true);
      setError(null);
      setResult(null);

      const response = await fetch(`${API_BASE}/api/v1/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          youtube_url: url,
          options: {}
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setJobId(data.job_id);

      // 상태 폴링 시작
      pollJobStatus(data.job_id);

    } catch (err) {
      setError(`처리 시작 실패: ${err.message}`);
      setIsProcessing(false);
    }
  };

  // 작업 상태 폴링
  const pollJobStatus = async (jobId) => {
    const maxAttempts = 300; // 10분 (2초 간격)
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/jobs/${jobId}/status`);
        if (!response.ok) {
          throw new Error(`Status check failed: ${response.status}`);
        }

        const statusData = await response.json();
        setStatus(statusData);

        if (statusData.status === 'completed') {
          // 결과 가져오기
          const resultResponse = await fetch(`${API_BASE}/api/v1/jobs/${jobId}/result`);
          if (resultResponse.ok) {
            const resultData = await resultResponse.json();
            setResult(resultData);
          }
          setIsProcessing(false);
          fetchJobs(); // 작업 목록 새로고침
        } else if (statusData.status === 'failed') {
          setError(statusData.error || '처리 중 오류가 발생했습니다.');
          setIsProcessing(false);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000); // 2초 후 재시도
        } else {
          setError('처리 시간이 너무 오래 걸립니다.');
          setIsProcessing(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000);
        } else {
          setError('상태 확인 실패');
          setIsProcessing(false);
        }
      }
    };

    poll();
  };

  // 모든 작업 목록 가져오기
  const fetchJobs = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/jobs`);
      if (response.ok) {
        const data = await response.json();
        setJobs(data.jobs || []);
      }
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    }
  };

  // 컴포넌트 마운트시 작업 목록 로드
  useEffect(() => {
    fetchJobs();
  }, []);

  // 결과 렌더링
  const renderResult = () => {
    if (!result || !result.sections) return null;

    return (
      <div className="result-container">
        <h3>📊 분석 결과</h3>
        <div className="sections">
          {result.sections.map((section, index) => (
            <div key={index} className="section">
              {section.type === 'paragraph' && (
                <div className="paragraph">
                  <p>{section.content}</p>
                </div>
              )}
              {(section.type === 'chart' || section.type === 'image') && section.src && (
                <div className="visual">
                  <img
                    src={section.src}
                    alt={`Visual ${index}`}
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'block';
                    }}
                  />
                  <div style={{display: 'none'}} className="error-placeholder">
                    이미지를 불러올 수 없습니다: {section.src}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎬 YouTube Reporter</h1>
        <p>YouTube 영상을 분석하여 시각적 보고서를 생성합니다</p>
      </header>

      <main className="main">
        <div className="input-section">
          <div className="url-input">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="YouTube URL을 입력하세요 (예: https://www.youtube.com/watch?v=...)"
              disabled={isProcessing}
            />
            <button
              onClick={processVideo}
              disabled={isProcessing || !url.trim()}
              className="process-btn"
            >
              {isProcessing ? '처리 중...' : '분석 시작'}
            </button>
          </div>

          {error && (
            <div className="error">
              ❌ {error}
            </div>
          )}
        </div>

        {status && (
          <div className="status-section">
            <h3>📋 처리 상태</h3>
            <div className="status-card">
              <div className="status-info">
                <span className={`status-badge ${status.status}`}>
                  {status.status === 'queued' && '대기 중'}
                  {status.status === 'processing' && '처리 중'}
                  {status.status === 'completed' && '완료'}
                  {status.status === 'failed' && '실패'}
                </span>
                <span className="status-message">{status.message}</span>
              </div>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{width: `${status.progress}%`}}
                ></div>
              </div>
              <small>작업 ID: {status.job_id}</small>
            </div>
          </div>
        )}

        {renderResult()}

        {jobs.length > 0 && (
          <div className="jobs-section">
            <h3>📜 작업 기록</h3>
            <div className="jobs-list">
              {jobs.slice().reverse().slice(0, 5).map((job) => (
                <div key={job.job_id} className="job-item">
                  <div className="job-header">
                    <span className={`status-badge ${job.status}`}>
                      {job.status}
                    </span>
                    <small>{new Date(job.created_at).toLocaleString()}</small>
                  </div>
                  <div className="job-url">{job.youtube_url}</div>
                  {job.status === 'completed' && (
                    <button
                      onClick={() => {
                        setJobId(job.job_id);
                        setStatus(job);
                        fetch(`${API_BASE}/api/v1/jobs/${job.job_id}/result`)
                          .then(r => r.json())
                          .then(setResult);
                      }}
                      className="view-result-btn"
                    >
                      결과 보기
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>YouTube Reporter v1.0.0 - Powered by Claude & FastAPI</p>
      </footer>
    </div>
  );
};

export default VideoProcessor;