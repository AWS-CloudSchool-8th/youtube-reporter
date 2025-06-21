// frontend/src/components/VideoInput.jsx
import React, { useState } from 'react';

const VideoInput = ({ onProcessVideo, isProcessing }) => {
  const [url, setUrl] = useState('');
  const [summaryLevel, setSummaryLevel] = useState('detailed');
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
    onProcessVideo(url, summaryLevel);
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
          <div className="summary-level-selector">
            <label htmlFor="summaryLevel">요약 레벨:</label>
            <select 
              id="summaryLevel"
              value={summaryLevel} 
              onChange={(e) => setSummaryLevel(e.target.value)}
              disabled={isProcessing}
              className="summary-select"
            >
              <option value="simple">간단 - 핵심만</option>
              <option value="detailed">상세 - 기본</option>
              <option value="expert">전문가 - 심화</option>
            </select>
          </div>
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
              '🔍 분석 시작'
            )}
          </button>
        </div>

        {error && <div className="error-message">❌ {error}</div>}
      </form>
    </div>
  );
};

export default VideoInput;