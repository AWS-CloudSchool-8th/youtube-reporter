// frontend/src/App_Debug_Enhanced.jsx
// 차트 렌더링 문제 디버깅 강화

import React, { useState, useEffect } from 'react';
import ChartRenderer from './components/charts/ChartRenderer.jsx';
import './App.css';

const App = () => {
  const [url, setUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [jobs, setJobs] = useState([]);

  const API_BASE = 'http://localhost:8000';

  const isValidYouTubeUrl = (url) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/;
    return youtubeRegex.test(url);
  };

  const processVideo = async () => {
    console.log('🎬 처리 시작:', url);

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
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('📋 작업 생성:', data);

      setJobId(data.job_id);
      pollJobStatus(data.job_id);

    } catch (err) {
      console.error('❌ 처리 실패:', err);
      setError(`처리 시작 실패: ${err.message}`);
      setIsProcessing(false);
    }
  };

  const pollJobStatus = async (jobId) => {
    const maxAttempts = 100;
    let attempts = 0;

    const poll = async () => {
      try {
        const statusResponse = await fetch(`${API_BASE}/api/v1/jobs/${jobId}/status`);
        if (!statusResponse.ok) {
          throw new Error(`Status check failed: ${statusResponse.status}`);
        }

        const statusData = await statusResponse.json();
        setStatus(statusData);

        if (statusData.status === 'completed') {
          console.log('✅ 작업 완료!');
          await loadJobResult(jobId);
          setIsProcessing(false);
          fetchJobs();

        } else if (statusData.status === 'failed') {
          setError(statusData.error || '처리 중 오류가 발생했습니다.');
          setIsProcessing(false);

        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 3000);
        } else {
          setError('처리 시간이 너무 오래 걸립니다.');
          setIsProcessing(false);
        }

      } catch (err) {
        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 5000);
        } else {
          setError(`상태 확인 실패: ${err.message}`);
          setIsProcessing(false);
        }
      }
    };

    poll();
  };

  const loadJobResult = async (jobId) => {
    try {
      console.log('📋 결과 로드:', jobId);

      const resultResponse = await fetch(`${API_BASE}/api/v1/jobs/${jobId}/result`);
      if (!resultResponse.ok) {
        throw new Error(`결과 가져오기 실패: ${resultResponse.status}`);
      }

      const resultData = await resultResponse.json();
      console.log('📄 결과 데이터:', resultData);

      // 섹션 타입별 개수 분석
      if (resultData.sections) {
        const typeCounts = {};
        resultData.sections.forEach(section => {
          typeCounts[section.type] = (typeCounts[section.type] || 0) + 1;
        });
        console.log('📊 섹션 타입별 개수:', typeCounts);
      }

      setResult(resultData);

    } catch (err) {
      console.error('❌ 결과 로드 실패:', err);
      setError(`결과 로드 실패: ${err.message}`);
    }
  };

  const fetchJobs = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/jobs`);
      if (response.ok) {
        const data = await response.json();
        setJobs(data.jobs || []);
      }
    } catch (err) {
      console.error('❌ 작업 목록 로드 실패:', err);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  // 개선된 결과 렌더링 - 각 섹션을 명확히 구분
  const renderResult = () => {
    if (!result) return null;

    console.log('🎨 결과 렌더링 시작');

    if (result.sections && Array.isArray(result.sections)) {
      // 섹션 타입별 통계
      const chartSections = result.sections.filter(s =>
        ['bar_chart', 'line_chart', 'pie_chart'].includes(s.type)
      );
      const textSections = result.sections.filter(s => s.type === 'paragraph');

      console.log(`📊 차트 섹션: ${chartSections.length}개, 텍스트 섹션: ${textSections.length}개`);

      return (
        <div className="result-container">
          <h3>📊 {result.title || '분석 결과'}</h3>

          {/* 통계 정보 */}
          <div style={{
            background: '#e8f5e8',
            padding: '15px',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <h4>📈 분석 통계</h4>
            <p>전체 섹션: {result.sections.length}개</p>
            <p>차트 섹션: {chartSections.length}개</p>
            <p>텍스트 섹션: {textSections.length}개</p>
          </div>

          <div className="sections">
            {result.sections.map((section, index) => {
              console.log(`🔍 섹션 ${index} 렌더링:`, section.type, section.title);

              return (
                <div key={section.id || index} className="section" style={{
                  border: section.type === 'paragraph' ? '2px solid #blue' : '2px solid #green',
                  margin: '15px 0',
                  padding: '15px',
                  borderRadius: '8px'
                }}>

                  {/* 섹션 헤더 */}
                  <div style={{
                    background: section.type === 'paragraph' ? '#e3f2fd' : '#e8f5e8',
                    padding: '10px',
                    marginBottom: '15px',
                    borderRadius: '4px'
                  }}>
                    <strong>섹션 {index + 1}: {section.type}</strong>
                    {section.title && <span> - {section.title}</span>}
                  </div>

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
                    section.type === 'pie_chart') && (
                    <div className="visual-chart">
                      <h4>{section.title}</h4>

                      {/* 차트 데이터 검증 */}
                      {section.data ? (
                        <div>
                          <div style={{ marginBottom: '10px', fontSize: '12px', color: '#666' }}>
                            <strong>차트 데이터:</strong>
                            <br />라벨: {section.data.labels ? section.data.labels.length : 0}개
                            <br />데이터셋: {section.data.datasets ? section.data.datasets.length : 0}개
                          </div>

                          <ChartRenderer
                            type={section.type}
                            data={{
                              labels: section.data.labels || [],
                              datasets: section.data.datasets || []
                            }}
                            title={section.title}
                          />
                        </div>
                      ) : (
                        <div style={{
                          background: '#fff3cd',
                          padding: '15px',
                          borderRadius: '4px',
                          border: '1px solid #ffeaa7'
                        }}>
                          ⚠️ 차트 데이터가 없습니다
                          <pre style={{ fontSize: '10px', marginTop: '5px' }}>
                            {JSON.stringify(section, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}

                  {/* 기타 타입 */}
                  {!['paragraph', 'bar_chart', 'line_chart', 'pie_chart'].includes(section.type) && (
                    <div style={{ background: '#fff3cd', padding: '15px', borderRadius: '4px' }}>
                      <p>🔧 지원되지 않는 타입: {section.type}</p>
                      <pre style={{ fontSize: '10px' }}>
                        {JSON.stringify(section, null, 2)}
                      </pre>
                    </div>
                  )}

                </div>
              );
            })}
          </div>
        </div>
      );
    }

    // 구형 형식 호환
    return (
      <div className="result-container">
        <h3>📊 분석 결과</h3>
        <div className="paragraph">
          <pre style={{ background: '#f8f9fa', padding: '15px', borderRadius: '8px', fontSize: '12px' }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </div>
    );
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎬 YouTube Reporter</h1>
        <p>차트 렌더링 디버깅 버전</p>
      </header>

      <main className="main">
        {/* 입력 섹션 */}
        <div className="input-section">
          <div className="url-input">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="YouTube URL을 입력하세요"
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

        {/* 상태 섹션 */}
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
                  style={{ width: `${status.progress || 0}%` }}
                />
              </div>
              <small>작업 ID: {status.job_id}</small>
            </div>
          </div>
        )}

        {/* 결과 섹션 */}
        {renderResult()}

        {/* 작업 기록 */}
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
                        console.log('🔍 결과 보기:', job.job_id);
                        loadJobResult(job.job_id);
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
        <p>YouTube Reporter v2.0.0 - 차트 디버깅 버전</p>
      </footer>
    </div>
  );
};

export default App;