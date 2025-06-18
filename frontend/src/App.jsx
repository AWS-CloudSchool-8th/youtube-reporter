// frontend/src/App.jsx (스마트 시각화 지원 버전)
import React, { useState, useEffect } from 'react';
import AdvancedVisualization from './components/visualizations/AdvancedVisualization.jsx';
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
    console.log('🎬 스마트 시각화 처리 시작:', url);

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
      console.log('📋 스마트 시각화 작업 생성:', data);

      setJobId(data.job_id);
      pollJobStatus(data.job_id);

    } catch (err) {
      console.error('❌ 처리 실패:', err);
      setError(`처리 시작 실패: ${err.message}`);
      setIsProcessing(false);
    }
  };

  const pollJobStatus = async (jobId) => {
    const maxAttempts = 120; // 6분 대기
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
          console.log('✅ 스마트 시각화 작업 완료!');
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
      console.log('📋 스마트 시각화 결과 로드:', jobId);

      const resultResponse = await fetch(`${API_BASE}/api/v1/jobs/${jobId}/result`);
      if (!resultResponse.ok) {
        throw new Error(`결과 가져오기 실패: ${resultResponse.status}`);
      }

      const resultData = await resultResponse.json();
      console.log('📄 스마트 시각화 결과 데이터:', resultData);

      // 시각화 타입별 분석
      if (resultData.sections) {
        const vizTypeAnalysis = analyzeVisualizationTypes(resultData.sections);
        console.log('📊 시각화 타입 분석:', vizTypeAnalysis);

        // 결과에 분석 정보 추가
        resultData.analysis = vizTypeAnalysis;
      }

      setResult(resultData);

    } catch (err) {
      console.error('❌ 결과 로드 실패:', err);
      setError(`결과 로드 실패: ${err.message}`);
    }
  };

  const analyzeVisualizationTypes = (sections) => {
    const analysis = {
      total: sections.length,
      byType: {},
      advanced: [],
      basic: []
    };

    sections.forEach(section => {
      const type = section.type;
      analysis.byType[type] = (analysis.byType[type] || 0) + 1;

      if (['bar_chart', 'line_chart', 'pie_chart'].includes(type)) {
        analysis.basic.push(type);
      } else if (!['paragraph', 'heading'].includes(type)) {
        analysis.advanced.push(type);
      }
    });

    return analysis;
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

  const renderResult = () => {
    if (!result) return null;

    console.log('🎨 스마트 시각화 결과 렌더링 시작');

    return (
      <div className="result-container">
        <h3>🧠 {result.title || '스마트 시각화 분석 결과'}</h3>

        {/* 분석 통계 정보 */}
        {result.analysis && (
          <div style={{
            background: 'linear-gradient(135deg, #e8f5e8 0%, #d4eedd 100%)',
            padding: '20px',
            borderRadius: '12px',
            marginBottom: '25px',
            border: '2px solid #10b981'
          }}>
            <h4 style={{ margin: '0 0 15px 0', color: '#065f46' }}>
              📈 스마트 분석 결과
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
              <div>
                <strong>전체 섹션:</strong> {result.analysis.total}개
              </div>
              <div>
                <strong>기본 차트:</strong> {result.analysis.basic.length}개
              </div>
              <div>
                <strong>고급 시각화:</strong> {result.analysis.advanced.length}개
              </div>
            </div>

            {result.analysis.advanced.length > 0 && (
              <div style={{ marginTop: '10px' }}>
                <strong>사용된 고급 시각화:</strong>{' '}
                <span style={{
                  background: '#10b981',
                  color: 'white',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  marginLeft: '5px'
                }}>
                  {[...new Set(result.analysis.advanced)].join(', ')}
                </span>
              </div>
            )}

            {/* 시각화 통계 (백엔드에서 제공되는 경우) */}
            {result.visualization_stats && (
              <div style={{ marginTop: '15px', fontSize: '14px', color: '#065f46' }}>
                <strong>생성 통계:</strong>
                텍스트 {result.visualization_stats.text_sections}개,
                차트 {result.visualization_stats.chart_sections}개,
                고급 {result.visualization_stats.advanced_viz}개
              </div>
            )}
          </div>
        )}

        {/* 시각화 섹션들 */}
        <div className="sections">
          {result.sections && result.sections.map((section, index) => {
            console.log(`🔍 섹션 ${index} 렌더링:`, section.type, section.title);

            return (
              <AdvancedVisualization
                key={section.id || index}
                section={section}
                index={index}
              />
            );
          })}
        </div>

        {/* 디버그 정보 (개발 모드) */}
        {process.env.NODE_ENV === 'development' && (
          <details style={{ marginTop: '30px' }}>
            <summary style={{
              cursor: 'pointer',
              padding: '10px',
              background: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #dee2e6'
            }}>
              🔧 개발자 정보 보기
            </summary>
            <pre style={{
              background: '#f8f9fa',
              padding: '15px',
              borderRadius: '8px',
              fontSize: '11px',
              overflow: 'auto',
              maxHeight: '300px',
              marginTop: '10px'
            }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
        )}
      </div>
    );
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🧠 YouTube Reporter</h1>
        <p>AI 기반 스마트 시각화 분석 플랫폼</p>
        <div style={{ fontSize: '14px', opacity: '0.8', marginTop: '10px' }}>
          마인드맵 • 플로우차트 • 타임라인 • 비교표 • 네트워크 다이어그램
        </div>
      </header>

      <main className="main">
        {/* 입력 섹션 */}
        <div className="input-section">
          <div className="url-input">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="YouTube URL을 입력하세요 (스마트 시각화가 자동 생성됩니다)"
              disabled={isProcessing}
            />
            <button
              onClick={processVideo}
              disabled={isProcessing || !url.trim()}
              className="process-btn"
            >
              {isProcessing ? (
                <span>
                  <span className="loading-spinner"></span>
                  분석 중...
                </span>
              ) : (
                '🧠 스마트 분석'
              )}
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
                  {status.status === 'queued' && '🔄 대기 중'}
                  {status.status === 'processing' && '🧠 분석 중'}
                  {status.status === 'completed' && '✅ 완료'}
                  {status.status === 'failed' && '❌ 실패'}
                </span>
                <span className="status-message">{status.message}</span>
              </div>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${status.progress || 0}%` }}
                />
              </div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '12px',
                color: '#666',
                marginTop: '8px'
              }}>
                <span>작업 ID: {status.job_id}</span>
                {status.visualization_stats && (
                  <span>
                    시각화: {status.visualization_stats.advanced_viz}개 고급, {status.visualization_stats.chart_sections}개 차트
                  </span>
                )}
              </div>
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
                      {job.status === 'completed' && '✅'}
                      {job.status === 'failed' && '❌'}
                      {job.status === 'processing' && '🧠'}
                      {job.status === 'queued' && '🔄'}
                      {' '}{job.status}
                    </span>
                    <small>{new Date(job.created_at).toLocaleString()}</small>
                  </div>

                  <div className="job-url">{job.youtube_url}</div>

                  {/* 시각화 통계 표시 */}
                  {job.visualization_stats && (
                    <div style={{
                      background: '#f8f9fa',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      fontSize: '12px',
                      margin: '8px 0',
                      color: '#495057'
                    }}>
                      📊 생성된 시각화:
                      {job.visualization_stats.advanced_viz > 0 && (
                        <span style={{ color: '#28a745', fontWeight: 'bold' }}>
                          {' '}고급 {job.visualization_stats.advanced_viz}개
                        </span>
                      )}
                      {job.visualization_stats.chart_sections > 0 && (
                        <span style={{ color: '#007bff', fontWeight: 'bold' }}>
                          {' '}차트 {job.visualization_stats.chart_sections}개
                        </span>
                      )}
                      {' '}텍스트 {job.visualization_stats.text_sections}개
                    </div>
                  )}

                  {job.status === 'completed' && (
                    <button
                      onClick={() => {
                        console.log('🔍 결과 보기:', job.job_id);
                        loadJobResult(job.job_id);
                      }}
                      className="view-result-btn"
                    >
                      🧠 스마트 결과 보기
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 기능 소개 섹션 (결과가 없을 때만 표시) */}
        {!result && !isProcessing && (
          <div className="features-section" style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            padding: '2rem',
            borderRadius: '20px',
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.15)',
            marginBottom: '2rem',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            <h3 style={{ textAlign: 'center', marginBottom: '1.5rem', color: '#1e293b' }}>
              🧠 스마트 시각화 기능
            </h3>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '1.5rem'
            }}>
              <div className="feature-card">
                <h4>🗺️ 마인드맵</h4>
                <p>개념과 아이디어의 연결 관계를 시각적으로 표현</p>
              </div>

              <div className="feature-card">
                <h4>📊 플로우차트</h4>
                <p>프로세스와 의사결정 과정을 단계별로 도식화</p>
              </div>

              <div className="feature-card">
                <h4>⏰ 타임라인</h4>
                <p>시간순 사건과 발전 과정을 시각적으로 정렬</p>
              </div>

              <div className="feature-card">
                <h4>📋 비교표</h4>
                <p>여러 항목의 특징과 차이점을 체계적으로 비교</p>
              </div>

              <div className="feature-card">
                <h4>🌳 계층구조</h4>
                <p>조직도나 분류체계를 트리 형태로 표현</p>
              </div>

              <div className="feature-card">
                <h4>🕸️ 네트워크</h4>
                <p>복잡한 관계와 연결고리를 네트워크로 시각화</p>
              </div>
            </div>

            <div style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              padding: '1rem',
              borderRadius: '12px',
              textAlign: 'center',
              marginTop: '1.5rem'
            }}>
              <strong>✨ AI가 영상 내용을 분석하여 가장 적합한 시각화를 자동 생성합니다</strong>
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>YouTube Reporter v3.0.0 - Smart Visualization Platform</p>
        <div style={{ fontSize: '12px', opacity: '0.8', marginTop: '5px' }}>
          Powered by AI • 실시간 분석 • 맞춤형 시각화
        </div>
      </footer>
    </div>
  );
};

export default App;