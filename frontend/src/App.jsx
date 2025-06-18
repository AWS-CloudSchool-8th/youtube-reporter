// frontend/src/App.jsx (깔끔하게 다시 작성)
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ChartRenderer from './components/charts/ChartRenderer.jsx';
import { napkinTheme } from './utils/napkinTheme.js';
import './App.css';

const App = () => {
  // 상태 관리
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
      setStatus(null);

      const response = await fetch(`${API_BASE}/api/v1/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
    const maxAttempts = 150; // 5분
    let attempts = 0;

    const poll = async () => {
      try {
        // 상태 확인
        const statusResponse = await fetch(`${API_BASE}/api/v1/jobs/${jobId}/status`);
        if (!statusResponse.ok) {
          throw new Error(`Status check failed: ${statusResponse.status}`);
        }

        const statusData = await statusResponse.json();
        setStatus(statusData);

        if (statusData.status === 'completed') {
          // 결과 가져오기
          await loadJobResult(jobId);
          setIsProcessing(false);
          fetchJobs();

        } else if (statusData.status === 'failed') {
          setError(statusData.error || '처리 중 오류가 발생했습니다.');
          setIsProcessing(false);

        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000);
        } else {
          setError('처리 시간이 너무 오래 걸립니다.');
          setIsProcessing(false);
        }

      } catch (err) {
        console.error('Polling error:', err);
        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 3000);
        } else {
          setError('상태 확인 실패');
          setIsProcessing(false);
        }
      }
    };

    poll();
  };

  // 작업 결과 로드
  const loadJobResult = async (jobId) => {
    try {
      console.log('🔍 작업 결과 로드 중:', jobId);

      // 1. Job 결과 가져오기
      const resultResponse = await fetch(`${API_BASE}/api/v1/jobs/${jobId}/result`);
      if (!resultResponse.ok) {
        throw new Error(`결과 가져오기 실패: ${resultResponse.status}`);
      }

      const resultData = await resultResponse.json();
      console.log('📋 Job 결과:', resultData);

      // 2. MVC 보고서가 있다면 상세 정보 가져오기
      if (resultData.report_id) {
        console.log('📊 보고서 상세 정보 로드 중:', resultData.report_id);

        const reportResponse = await fetch(`${API_BASE}/api/v1/reports/${resultData.report_id}`);
        if (reportResponse.ok) {
          const reportData = await reportResponse.json();
          console.log('✅ 보고서 데이터:', reportData);
          setResult(reportData);
        } else {
          console.log('⚠️ 보고서 로드 실패, Job 결과 사용');
          setResult(resultData);
        }
      } else {
        console.log('📄 직접 결과 사용');
        setResult(resultData);
      }

    } catch (err) {
      console.error('❌ 결과 로드 실패:', err);
      setError(`결과 로드 실패: ${err.message}`);
    }
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
      console.error('작업 목록 가져오기 실패:', err);
    }
  };

  // 컴포넌트 마운트시 작업 목록 로드
  useEffect(() => {
    fetchJobs();
  }, []);

  // 결과 렌더링
  const renderResult = () => {
    if (!result) return null;

    // MVC 결과 (sections 배열)
    if (result.sections && Array.isArray(result.sections)) {
      return (
        <motion.div
          className="result-container"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h3>📊 분석 결과</h3>
          <div className="sections">
            {result.sections.map((section, index) => (
              <motion.div
                key={section.id || index}
                className="section"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                {/* 텍스트 섹션 */}
                {section.type === 'paragraph' && (
                  <div className="paragraph">
                    {section.title && <h4>{section.title}</h4>}
                    <p>{section.content}</p>
                  </div>
                )}

                {/* 차트 섹션 */}
                {(section.type === 'bar_chart' ||
                  section.type === 'line_chart' ||
                  section.type === 'pie_chart') && section.data && (
                  <div className="visual-chart">
                    <ChartRenderer
                      type={section.type}
                      data={section.data}
                      title={section.title}
                      className="chart-section"
                    />
                  </div>
                )}

                {/* 이미지 섹션 */}
                {section.type === 'image' && section.src && (
                  <div className="visual">
                    <img
                      src={section.src}
                      alt={section.title || `Visual ${index}`}
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
              </motion.div>
            ))}
          </div>
        </motion.div>
      );
    }

    // 기존 결과 형식 (호환성)
    if (result.sections && !Array.isArray(result.sections)) {
      return (
        <div className="result-container">
          <h3>📊 분석 결과</h3>
          <div className="paragraph">
            <p>{JSON.stringify(result, null, 2)}</p>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="app">
      {/* 헤더 */}
      <header className="header">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          🎬 YouTube Reporter
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          YouTube 영상을 분석하여 인터랙티브 보고서를 생성합니다
        </motion.p>
      </header>

      <main className="main">
        {/* 입력 섹션 */}
        <motion.div
          className="input-section"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="url-input">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="YouTube URL을 입력하세요 (예: https://www.youtube.com/watch?v=...)"
              disabled={isProcessing}
            />
            <motion.button
              onClick={processVideo}
              disabled={isProcessing || !url.trim()}
              className="process-btn"
              whileHover={{ scale: isProcessing ? 1 : 1.02 }}
              whileTap={{ scale: isProcessing ? 1 : 0.98 }}
            >
              {isProcessing ? '처리 중...' : '분석 시작'}
            </motion.button>
          </div>

          {/* 에러 메시지 */}
          <AnimatePresence>
            {error && (
              <motion.div
                className="error"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                ❌ {error}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* 상태 섹션 */}
        <AnimatePresence>
          {status && (
            <motion.div
              className="status-section"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
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
                  <motion.div
                    className="progress-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${status.progress || 0}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <small>작업 ID: {status.job_id}</small>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 결과 섹션 */}
        {renderResult()}

        {/* 작업 기록 */}
        {jobs.length > 0 && (
          <motion.div
            className="jobs-section"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <h3>📜 작업 기록</h3>
            <div className="jobs-list">
              {jobs.slice().reverse().slice(0, 5).map((job, index) => (
                <motion.div
                  key={job.job_id}
                  className="job-item"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <div className="job-header">
                    <span className={`status-badge ${job.status}`}>
                      {job.status}
                    </span>
                    <small>{new Date(job.created_at).toLocaleString()}</small>
                  </div>
                  <div className="job-url">{job.youtube_url}</div>

                  {job.status === 'completed' && (
                    <motion.button
                      onClick={() => loadJobResult(job.job_id)}
                      className="view-result-btn"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      결과 보기
                    </motion.button>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </main>

      {/* 푸터 */}
      <footer className="footer">
        <p>YouTube Reporter v2.0.0 - MVC Pattern + Chart.js</p>
      </footer>
    </div>
  );
};

export default App;