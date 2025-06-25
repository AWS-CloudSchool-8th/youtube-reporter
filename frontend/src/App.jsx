// frontend/src/App.jsx - 최신 백엔드 완전 호환 버전
import React, { useState, useEffect } from 'react';
import VideoInput from './components/VideoInput';
import StatusDisplay from './components/StatusDisplay';
import ResultViewer from './components/ResultViewer';
import './App.css';

const App = () => {
  const [currentJob, setCurrentJob] = useState(null);
  const [jobHistory, setJobHistory] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // URL 유효성 검증 (백엔드 검증 사용)
  const validateYouTubeUrl = async (url) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/validate-url?url=${encodeURIComponent(url)}`);
      const data = await response.json();
      return data.is_valid;
    } catch (error) {
      console.warn('URL 검증 실패, 클라이언트 검증 사용:', error);
      // 폴백: 클라이언트 검증
      const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/;
      return youtubeRegex.test(url);
    }
  };

  // 영상 처리 시작
  const handleProcessVideo = async (url) => {
    try {
      setError(null);
      setResult(null);
      setCurrentJob(null);

      console.log('🎬 영상 처리 시작:', url);

      // 1. URL 유효성 검증
      const isValidUrl = await validateYouTubeUrl(url);
      if (!isValidUrl) {
        setError('유효하지 않은 YouTube URL입니다. 올바른 형식으로 입력해주세요.');
        return;
      }

      // 2. 즉시 시작 알림 표시
      setCurrentJob({
        job_id: 'starting...',
        status: 'starting',
        progress: 0,
        message: '🚀 분석을 시작합니다...',
        created_at: new Date().toISOString()
      });

      // 3. 처리 요청
      const response = await fetch(`${API_BASE}/api/v1/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          youtube_url: url,
          options: {
            include_timestamp: true,
            detailed_analysis: true
          }
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '처리 요청 실패' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('📋 작업 생성:', data);

      setCurrentJob({
        job_id: data.job_id,
        status: data.status,
        progress: 5,
        message: data.message,
        created_at: data.created_at || new Date().toISOString()
      });

      // 4. 상태 폴링 시작
      pollJobStatus(data.job_id);

    } catch (error) {
      console.error('❌ 영상 처리 시작 실패:', error);
      setError(`처리 시작 실패: ${error.message}`);
    }
  };

  // 작업 상태 폴링 (개선된 버전)
  const pollJobStatus = async (jobId) => {
    const maxAttempts = 120; // 6분 대기 (3초 간격)
    let attempts = 0;
    let consecutiveErrors = 0;

    const poll = async () => {
      try {
        console.log(`🔍 상태 확인 ${attempts + 1}/${maxAttempts}:`, jobId);

        const statusResponse = await fetch(`${API_BASE}/api/v1/jobs/${jobId}/status`);

        if (!statusResponse.ok) {
          if (statusResponse.status === 404) {
            throw new Error('작업을 찾을 수 없습니다.');
          }
          throw new Error(`상태 확인 실패: HTTP ${statusResponse.status}`);
        }

        const statusData = await statusResponse.json();
        console.log('📊 상태 업데이트:', statusData);

        setCurrentJob(statusData);
        consecutiveErrors = 0; // 성공 시 에러 카운터 리셋

        if (statusData.status === 'completed') {
          console.log('✅ 작업 완료, 결과 로드 중...');
          await loadJobResult(jobId);
          fetchJobHistory();
        } else if (statusData.status === 'failed') {
          console.error('❌ 작업 실패:', statusData.error);
          setError(statusData.error || '처리 중 오류가 발생했습니다.');
        } else if (['processing', 'queued'].includes(statusData.status)) {
          if (attempts < maxAttempts) {
            attempts++;
            setTimeout(poll, 3000);
          } else {
            setError('처리 시간이 너무 오래 걸립니다. 잠시 후 다시 시도해주세요.');
          }
        }

      } catch (error) {
        console.error('🔍 상태 확인 오류:', error);
        consecutiveErrors++;

        if (consecutiveErrors >= 3) {
          setError(`연속된 상태 확인 실패: ${error.message}`);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 5000); // 오류 시 더 긴 간격
        } else {
          setError(`상태 확인 최종 실패: ${error.message}`);
        }
      }
    };

    poll();
  };

  // 결과 로드 (개선된 버전)
  const loadJobResult = async (jobId) => {
    try {
      console.log('📄 결과 로드 중:', jobId);

      const resultResponse = await fetch(`${API_BASE}/api/v1/jobs/${jobId}/result`);

      if (resultResponse.status === 202) {
        console.log('⏳ 아직 처리 중...');
        return;
      }

      if (!resultResponse.ok) {
        const errorData = await resultResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || `결과 로드 실패: HTTP ${resultResponse.status}`);
      }

      const resultData = await resultResponse.json();
      console.log('📊 결과 로드 완료:', resultData);

      setResult(resultData);

    } catch (error) {
      console.error('❌ 결과 로드 실패:', error);
      setError(`결과 로드 실패: ${error.message}`);
    }
  };

  // 작업 기록 가져오기 (개선된 버전)
  const fetchJobHistory = async () => {
    try {
      console.log('📜 작업 기록 로드 중...');

      const response = await fetch(`${API_BASE}/api/v1/jobs?limit=10`);
      if (response.ok) {
        const data = await response.json();
        console.log('📋 작업 기록 로드 완료:', data);
        setJobHistory(data || []);
      }
    } catch (error) {
      console.error('❌ 작업 기록 로드 실패:', error);
    }
  };

  // 이전 결과 보기
  const viewPreviousResult = async (jobId) => {
    try {
      console.log('👀 이전 결과 보기:', jobId);
      await loadJobResult(jobId);
    } catch (error) {
      setError(`결과 로드 실패: ${error.message}`);
    }
  };

  // 시스템 정보 로드
  const fetchSystemInfo = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/system-info`);
      if (response.ok) {
        const data = await response.json();
        setSystemInfo(data);
        console.log('🔧 시스템 정보:', data);
      }
    } catch (error) {
      console.warn('⚠️ 시스템 정보 로드 실패:', error);
    }
  };

  // API 상태 확인 (개선된 버전)
  const checkApiHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/`);
      if (response.ok) {
        const data = await response.json();
        console.log('✅ API 연결 확인:', data);
        return true;
      }
      return false;
    } catch (error) {
      console.warn('⚠️ API 연결 확인 실패:', error);
      setError('서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.');
      return false;
    }
  };

  // 새 분석 시작
  const startNewAnalysis = () => {
    setCurrentJob(null);
    setResult(null);
    setError(null);
  };

  // 에러 해제
  const dismissError = () => {
    setError(null);
  };

  // 초기화
  useEffect(() => {
    const initialize = async () => {
      const isHealthy = await checkApiHealth();
      if (isHealthy) {
        await fetchJobHistory();
        await fetchSystemInfo();
      }
    };

    initialize();
  }, []);

  const isProcessing = currentJob && ['processing', 'queued'].includes(currentJob.status);

  return (
    <div className="app">
      <header className="header">
        <h1>🎬 YouTube Reporter</h1>
        <p>AI 기반 YouTube 영상 분석 및 스마트 시각화 도구</p>
        <div className="header-subtitle">
          컨텍스트 기반 분석 • 자동 시각화 생성 • 포괄적 리포트
        </div>
        {systemInfo && (
          <div className="system-status">
            v{systemInfo.application?.version} •
            {systemInfo.configuration?.features_enabled?.aws_bedrock ? ' ✅ Claude AI' : ' ❌ Claude AI'} •
            {systemInfo.configuration?.features_enabled?.vidcap_api ? ' ✅ 자막 API' : ' ❌ 자막 API'}
          </div>
        )}
      </header>

      <main className="main">
        {/* 영상 입력 */}
        <VideoInput
          onProcessVideo={handleProcessVideo}
          isProcessing={isProcessing}
          validateUrl={validateYouTubeUrl}
        />

        {/* 에러 표시 */}
        {error && (
          <div className="error-section">
            <div className="error-content">
              <h4>❌ 오류 발생</h4>
              <p>{error}</p>
              <div className="error-actions">
                <button onClick={dismissError} className="error-dismiss">
                  확인
                </button>
                {!isProcessing && (
                  <button onClick={startNewAnalysis} className="error-retry">
                    🔄 다시 시도
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 상태 표시 */}
        {currentJob && (
          <StatusDisplay
            job={currentJob}
            onCancel={() => setCurrentJob(null)}
          />
        )}

        {/* 결과 표시 */}
        {result && (
          <ResultViewer
            result={result}
            onNewAnalysis={startNewAnalysis}
          />
        )}

        {/* 작업 기록 */}
        {jobHistory.length > 0 && !currentJob && !result && (
          <div className="job-history">
            <h3>📜 최근 작업 기록</h3>
            <div className="job-list">
              {jobHistory
                .slice(0, 5)
                .map((job) => (
                  <div key={job.job_id} className="job-item">
                    <div className="job-header">
                      <span className={`status-badge ${job.status}`}>
                        {job.status === 'completed' && '✅'}
                        {job.status === 'failed' && '❌'}
                        {job.status === 'processing' && '⚙️'}
                        {job.status === 'queued' && '🔄'}
                        {' '}{job.status}
                      </span>
                      <small className="job-time">
                        {new Date(job.created_at).toLocaleString('ko-KR')}
                      </small>
                    </div>

                    <div className="job-message">{job.message}</div>

                    {job.status === 'completed' && (
                      <button
                        onClick={() => viewPreviousResult(job.job_id)}
                        className="view-result-btn"
                      >
                        📊 결과 보기
                      </button>
                    )}

                    {job.status === 'failed' && job.error && (
                      <div className="job-error">
                        <strong>오류:</strong> {job.error}
                      </div>
                    )}
                  </div>
                ))}
            </div>

            {jobHistory.length > 5 && (
              <div className="job-more">
                총 {jobHistory.length}개 작업 중 최근 5개 표시
              </div>
            )}
          </div>
        )}

        {/* 상태가 없을 때 도움말 */}
        {!currentJob && !result && !error && (
          <div className="help-section">
            <h3>🚀 시작하기</h3>
            <div className="help-content">
              <div className="help-step">
                <span className="step-number">1</span>
                <div className="step-content">
                  <h4>YouTube URL 입력</h4>
                  <p>분석하고 싶은 YouTube 영상의 URL을 입력하세요</p>
                </div>
              </div>

              <div className="help-step">
                <span className="step-number">2</span>
                <div className="step-content">
                  <h4>AI가 자동 분석</h4>
                  <p>Claude AI가 영상 내용을 완전히 이해할 수 있는 상세한 요약 생성</p>
                </div>
              </div>

              <div className="help-step">
                <span className="step-number">3</span>
                <div className="step-content">
                  <h4>스마트 시각화</h4>
                  <p>내용에 맞는 최적의 차트, 다이어그램, 표를 자동 생성</p>
                </div>
              </div>

              <div className="help-step">
                <span className="step-number">4</span>
                <div className="step-content">
                  <h4>포괄적 리포트</h4>
                  <p>텍스트와 시각화가 완벽하게 통합된 리포트 확인</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>YouTube Reporter v2.0.0 - Smart Visualization Edition</p>
        <div className="footer-links">
          <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer">
            📖 API 문서
          </a>
          <span>•</span>
          <span>🧠 Powered by LangGraph & Claude AI</span>
          <span>•</span>
          <span>📊 Smart Context-based Visualization</span>
          {systemInfo && (
            <>
              <span>•</span>
              <span>🌍 {systemInfo.application?.name}</span>
            </>
          )}
        </div>
      </footer>
    </div>
  );
};

export default App;