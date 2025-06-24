# 🎬 YouTube Reporter v2.0 - Smart Visualization Edition

AI 기반 YouTube 영상 분석 및 스마트 시각화 도구입니다. 영상을 보지 않고도 완전히 이해할 수 있는 포괄적 요약과 내용에 최적화된 시각화를 자동으로 생성합니다.

## ✨ 주요 특징

### 🧠 포괄적 요약 생성
- **완전한 이해**: 영상을 보지 않아도 모든 내용을 이해할 수 있는 상세 요약
- **구조화된 내용**: 논리적 흐름으로 체계적으로 정리
- **맥락 제공**: 배경 정보와 전제 조건까지 포함

### 🎨 스마트 시각화 시스템
- **컨텍스트 분석**: AI가 내용을 깊이 분석하여 시각화 기회 자동 탐지
- **최적 시각화 선택**: 내용에 따라 가장 효과적인 시각화 타입 자동 결정
- **다양한 형식 지원**:
  - 📊 차트 (막대, 선, 파이, 레이더, 산점도)
  - 🔄 다이어그램 (플로우차트, 타임라인, 마인드맵)
  - 📋 테이블 (비교표, 데이터 테이블)
  - 🎯 고급 시각화 (네트워크, 히트맵 등)

### 🚀 향상된 사용자 경험
- **실시간 진행 상황**: 각 처리 단계별 상세 피드백
- **통합 리포트**: 텍스트와 시각화가 완벽하게 결합된 리포트
- **반응형 디자인**: 모든 디바이스에서 최적화된 경험

## 🏗️ 아키텍처

```
YouTube Reporter v2.0
├── Backend (FastAPI + LangGraph)
│   ├── Caption Agent: 자막 추출
│   ├── Summary Agent: 포괄적 요약 생성
│   ├── Visual Agent: 스마트 시각화 생성
│   └── Report Agent: 최종 리포트 조합
│
└── Frontend (React)
    ├── VideoInput: URL 입력
    ├── StatusDisplay: 실시간 상태
    ├── SmartVisualization: 다양한 시각화 렌더링
    └── ResultViewer: 통합 리포트 표시
```

## 📦 설치 방법

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd youtube-reporter
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
```

`.env` 파일 편집:
```env
# 필수 설정
VIDCAP_API_KEY=your_vidcap_api_key_here
AWS_REGION=us-west-2
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# AWS 인증 (AWS CLI 설정이 없는 경우)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### 3. 백엔드 설정
```bash
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 4. 프론트엔드 설정
```bash
cd frontend
npm install
cd ..
```

## 🚀 실행 방법

### 방법 1: 개별 실행

**터미널 1 - 백엔드 서버:**
```bash
python main.py
```

**터미널 2 - 프론트엔드 서버:**
```bash
cd frontend
npm start
```

### 방법 2: 동시 실행 (추천)
```bash
# 백엔드와 프론트엔드를 동시에 실행하는 스크립트 작성
# run.sh (Linux/Mac) 또는 run.bat (Windows)
```

## 📱 사용 방법

1. **웹 브라우저 접속**: http://localhost:3000
2. **YouTube URL 입력**: 분석할 영상의 URL 입력
3. **분석 시작**: "🎯 스마트 분석 시작" 버튼 클릭
4. **진행 상황 확인**: 실시간으로 처리 단계 확인
   - 📝 자막 추출
   - 🧠 내용 분석
   - 🎨 시각화 생성
   - 📊 리포트 작성
5. **결과 확인**: 포괄적 요약과 스마트 시각화가 포함된 리포트 확인

## 🔧 API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| `GET` | `/` | API 문서로 리다이렉트 |
| `GET` | `/health` | 서비스 상태 확인 |
| `GET` | `/api/v1/` | API 정보 |
| `POST` | `/api/v1/process` | 영상 처리 시작 |
| `GET` | `/api/v1/jobs/{job_id}/status` | 작업 상태 조회 |
| `GET` | `/api/v1/jobs/{job_id}/result` | 작업 결과 조회 |
| `GET` | `/api/v1/jobs` | 작업 목록 조회 |

**API 문서**: http://localhost:8000/docs

## 📊 시각화 예제

### 차트 (Chart.js)
```javascript
{
  type: "chart",
  library: "chartjs",
  config: {
    type: "bar",
    data: {
      labels: ["항목1", "항목2", "항목3"],
      datasets: [{
        label: "데이터",
        data: [10, 20, 30]
      }]
    }
  }
}
```

### 다이어그램 (Mermaid)
```javascript
{
  type: "diagram",
  library: "mermaid",
  code: "graph TD\n  A[시작] --> B[처리]\n  B --> C[완료]"
}
```

### 테이블
```javascript
{
  type: "table",
  headers: ["항목", "값", "설명"],
  rows: [
    ["항목1", "10", "설명1"],
    ["항목2", "20", "설명2"]
  ]
}
```

## 🛠️ 기술 스택

### Backend
- **FastAPI**: 고성능 웹 프레임워크
- **LangGraph**: AI 에이전트 워크플로우
- **LangChain**: LLM 추상화 레이어
- **Claude AI (AWS Bedrock)**: 텍스트 분석 및 생성
- **VidCap API**: YouTube 자막 추출

### Frontend
- **React 18**: 최신 React 기능 활용
- **Chart.js**: 다양한 차트 시각화
- **Mermaid**: 다이어그램 생성
- **CSS3**: 모던한 스타일링

## 🔍 문제 해결

### 1. 자막 추출 실패
- YouTube 영상에 자막이 있는지 확인
- VidCap API 키가 올바른지 확인
- 한국어 자막이 있는 영상 권장

### 2. AWS Bedrock 오류
```bash
# AWS 자격 증명 확인
aws configure list

# Bedrock 모델 확인
aws bedrock list-foundation-models --region us-west-2
```

### 3. 프론트엔드 연결 실패
- 백엔드 서버가 실행 중인지 확인
- CORS 설정 확인
- 포트 충돌 확인 (8000, 3000)

## 📈 성능 최적화

- **자막 전처리**: 긴 자막은 중요 부분만 추출
- **비동기 처리**: 백그라운드 작업으로 응답 속도 향상
- **캐싱**: 작업 결과 메모리 캐싱
- **컴포넌트 최적화**: React 컴포넌트 lazy loading

## 🤝 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🙏 감사의 말

- Anthropic Claude AI
- LangChain & LangGraph 커뮤니티
- Chart.js, Mermaid.js 개발자들
- 모든 오픈소스 기여자들

---

**Made with ❤️ by YouTube Reporter Team**