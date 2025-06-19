// frontend/src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// 루트 엘리먼트 가져오기
const root = ReactDOM.createRoot(document.getElementById('root'));

// 개발 환경에서는 StrictMode 사용, 프로덕션에서는 제거
const AppComponent = process.env.NODE_ENV === 'development' ? (
  <React.StrictMode>
    <App />
  </React.StrictMode>
) : (
  <App />
);

// React 앱 렌더링
root.render(AppComponent);

// Web Vitals 측정 (선택사항)
// 성능 메트릭을 측정하고 로그를 남깁니다
// 자세한 내용: https://bit.ly/CRA-vitals
reportWebVitals(console.log);

// 에러 바운더리 (전역 에러 처리)
window.addEventListener('error', (event) => {
  console.error('전역 에러 발생:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('처리되지 않은 Promise 거부:', event.reason);
});

// 서비스 워커 등록 (PWA 지원)
if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('Service Worker 등록 성공:', registration.scope);
      })
      .catch((error) => {
        console.log('Service Worker 등록 실패:', error);
      });
  });
}