// frontend/src/components/VideoInput.jsx - 백엔드 API 완전 호환 버전
import React, { useState, useEffect } from 'react';

const VideoInput = ({ onProcessVideo, isProcessing, validateUrl }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [validating, setValidating] = useState(false);
  const [isValid, setIsValid] = useState(null);
  const [recentUrls, setRecentUrls] = useState([]);

  // 로컬 스토리지에서 최근 URL 로드
  useEffect(() => {
    const saved = localStorage.getItem('youtube-reporter-recent-urls');
    if (saved) {
      try {
        setRecentUrls(JSON.parse(saved));
      } catch (e) {
        console.warn('최근 URL 로드 실패:', e);
      }
    }
  }, []);

  // URL 변경 시 실시간 검증
  useEffect(() => {
    if (!url.trim()) {
      setIsValid(null);
      setError('');
      return;
    }

    const debounceTimer = setTimeout(async () => {
      if (url.trim() && validateUrl) {
        setValidating(true);
        try {
          const valid = await validateUrl(url);
          setIsValid(valid);
          if (!valid) {
            setError('올바른 YouTube URL 형식이 아닙니다.');
          } else {
            setError('');
          }
        } catch (err) {
          console.warn('URL 검증 실패:', err);
          // 폴백: 클라이언트 검증
          const valid = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/.test(url);
          setIsValid(valid);
          if (!valid) {
            setError('올바른 YouTube URL 형식이 아닙니다.');
          } else {
            setError('');
          }
        }
        setValidating(false);
      }
    }, 500); // 500ms 디바운스

    return () => clearTimeout(debounceTimer);
  }, [url, validateUrl]);

  const saveRecentUrl = (url) => {
    const newRecent = [url, ...recentUrls.filter(u => u !== url)].slice(0, 5);
    setRecentUrls(newRecent);
    localStorage.setItem('youtube-reporter-recent-urls', JSON.stringify(newRecent));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!url.trim()) {
      setError('YouTube URL을 입력해주세요.');
      return;
    }

    if (isValid === false) {
      setError('올바른 YouTube URL을 입력해주세요.');
      return;
    }

    setError('');
    saveRecentUrl(url);
    onProcessVideo(url);
  };

  const handleUrlSelect = (selectedUrl) => {
    setUrl(selectedUrl);
  };

  const clearUrl = () => {
    setUrl('');
    setError('');
    setIsValid(null);
  };

  const pasteFromClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text);
      }
    } catch (err) {
      console.warn('클립보드 접근 실패:', err);
    }
  };

  const getUrlStatus = () => {
    if (validating) return { icon: '🔄', class: 'validating', text: '검증 중...' };
    if (isValid === true) return { icon: '✅', class: 'valid', text: '유효한 URL' };
    if (isValid === false) return { icon: '❌', class: 'invalid', text: '잘못된 URL' };
    return null;
  };

  const urlStatus = getUrlStatus();

  return (
    <div className="video-input-section">
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <div className="url-input-container">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="YouTube URL을 입력하세요 (예: https://www.youtube.com/watch?v=...)"
              disabled={isProcessing}
              className={`url-input ${urlStatus?.class || ''}`}
            />

            {/* URL 상태 표시 */}
            {urlStatus && (
              <div className={`url-status ${urlStatus.class}`}>
                <span className="status-icon">{urlStatus.icon}</span>
                <span className="status-text">{urlStatus.text}</span>
              </div>
            )}

            {/* URL 입력 도구 */}
            <div className="input-tools">
              {url && (
                <button
                  type="button"
                  onClick={clearUrl}
                  className="tool-btn clear-btn"
                  title="입력 내용 지우기"
                >
                  ✕
                </button>
              )}
              <button
                type="button"
                onClick={pasteFromClipboard}
                className="tool-btn paste-btn"
                title="클립보드에서 붙여넣기"
              >
                📋
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isProcessing || !url.trim() || isValid === false || validating}
            className={`process-btn ${isValid === true ? 'ready' : ''}`}
          >
            {isProcessing ? (
              <>
                <span className="loading-spinner"></span>
                분석 중...
              </>
            ) : (
              <>
                🎯 스마트 분석 시작
              </>
            )}
          </button>
        </div>

        {/* 에러 메시지 */}
        {error && <div className="error-message">❌ {error}</div>}

        {/* 최근 URL 목록 */}
        {recentUrls.length > 0 && !isProcessing && (
          <div className="recent-urls">
            <h4>📝 최근 사용한 URL</h4>
            <div className="url-list">
              {recentUrls.map((recentUrl, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleUrlSelect(recentUrl)}
                  className="recent-url-btn"
                  title={recentUrl}
                >
                  🎬 {recentUrl.length > 50 ? recentUrl.substring(0, 47) + '...' : recentUrl}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 정보 섹션 */}
        <div className="input-info">
          <p>🤖 AI가 영상을 분석하여 다음을 자동으로 생성합니다:</p>
          <ul>
            <li>📝 영상을 보지 않고도 이해할 수 있는 상세한 요약</li>
            <li>📊 내용에 맞는 최적의 시각화 (차트, 다이어그램, 표 등)</li>
            <li>💡 핵심 인사이트와 실행 가능한 조언</li>
            <li>🎯 컨텍스트 기반 스마트 분석</li>
          </ul>
        </div>

        {/* 지원되는 URL 형식 */}
        <details className="url-formats">
          <summary>지원되는 YouTube URL 형식</summary>
          <div className="format-examples">
            <p>✅ https://www.youtube.com/watch?v=VIDEO_ID</p>
            <p>✅ https://youtu.be/VIDEO_ID</p>
            <p>✅ https://youtube.com/embed/VIDEO_ID</p>
            <p>✅ https://m.youtube.com/watch?v=VIDEO_ID</p>
          </div>
        </details>
      </form>
    </div>
  );
};

export default VideoInput;