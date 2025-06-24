// frontend/src/components/VideoInput.jsx
import React, { useState } from 'react';

const VideoInput = ({ onProcessVideo, isProcessing }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const isValidYouTubeUrl = (url) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/;
    return youtubeRegex.test(url);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!url.trim()) {
      setError('YouTube URL을 입력해주세요.');
      return;
    }

    if (!isValidYouTubeUrl(url)) {
      setError('올바른 YouTube URL을 입력해주세요.');
      return;
    }

    setError('');
    onProcessVideo(url);
  };

  return (
    <div className="video-input-section">
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="YouTube URL을 입력하세요 (예: https://www.youtube.com/watch?v=...)"
            disabled={isProcessing}
            className="url-input"
          />
          <button
            type="submit"
            disabled={isProcessing || !url.trim()}
            className="process-btn"
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

        {error && <div className="error-message">❌ {error}</div>}

        <div className="input-info">
          <p>🤖 AI가 영상을 분석하여 다음을 자동으로 생성합니다:</p>
          <ul>
            <li>📝 영상을 보지 않고도 이해할 수 있는 상세한 요약</li>
            <li>📊 내용에 맞는 최적의 시각화 (차트, 다이어그램, 표 등)</li>
            <li>💡 핵심 인사이트와 실행 가능한 조언</li>
          </ul>
        </div>
      </form>
    </div>
  );
};

export default VideoInput;