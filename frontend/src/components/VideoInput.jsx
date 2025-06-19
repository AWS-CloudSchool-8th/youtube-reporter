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