# YouTube Reporter v2.0

AI 기반 YouTube 영상 분석 및 스마트 시각화 도구

## 🌟 주요 기능

- **포괄적 요약**: Claude AI가 영상 내용을 완전히 이해할 수 있는 상세한 요약 생성
- **스마트 시각화**: 내용에 맞는 최적의 차트, 다이어그램, 표를 자동 생성
- **컨텍스트 기반 분석**: 영상의 맥락을 파악하여 적절한 시각화 제안
- **다양한 시각화 타입**: Chart.js, Mermaid, 테이블 등 다양한 형태 지원

## 🏗️ 프로젝트 구조

```
youtube-reporter/
├── app/
│   ├── agents/          # LangGraph 에이전트들 (yesol 브랜치 코드)
│   │   ├── caption_agent.py
│   │   ├── summary_agent.py
│   │   ├── visual_agent.py
│   │   ├── report_agent.py
│   │   └── graph_workflow.py
│   ├── api/             # FastAPI 라우터들 (yesol-v2 구조)
│   │   └── youtube.py
│   ├── core/            # 핵심 설정 및 의존성
│   │   ├── config.py
│   │   └── dependencies.py
│   ├── models/          # Pydantic 모델들
│   │   ├── request.py
│   │   └── response.py
│   ├── services/        # 비즈니스 로직
│   │   ├── youtube_service.py
│   │   └── langgraph_service.py
│   └── utils/           # 유틸리티 함수들
│       ├── config.py
│       ├── logger.py
│       └── helpers.py
├── frontend/            # React 프론트엔드 (yesol-v2)
│   ├── src/
│   │   ├── components/
│   │   │   ├── VideoInput.jsx
│   │   │   ├── StatusDisplay.jsx
│   │   │   ├── ResultViewer.jsx
│   │   │   └── SmartVisualization.jsx
│   │   └── App.jsx
│   └── package.json
├── main.py              # 메인 실행 파일
├── requirements.txt
└── .env.example
```

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd youtube-reporter

# Python 가상환경 생성
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env.example을 .env로 복사
copy .env.example .env

# .env 파일 편집하여 실제 값 입력
```

필수 환경 변수:
- `VIDCAP_API_KEY`: YouTube 자막 추출용 API 키
- `AWS_REGION`: AWS 리전 (예: us-west-2)
- `BEDROCK_MODEL_ID`: Claude 모델 ID
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS 인증 정보

### 3. 백엔드 실행

```bash
# 메인 디렉토리에서
python main.py
```

서버가 http://localhost:8000 에서 실행됩니다.

### 4. 프론트엔드 실행

```bash
# 새 터미널에서
cd frontend
npm install
npm start
```

프론트엔드가 http://localhost:3000 에서 실행됩니다.

## 🔧 API 엔드포인트

- `POST /api/v1/process`: 영상 처리 시작
- `GET /api/v1/jobs/{job_id}/status`: 작업 상태 조회
- `GET /api/v1/jobs/{job_id}/result`: 작업 결과 조회
- `GET /api/v1/jobs`: 작업 목록 조회
- `GET /docs`: API 문서 (Swagger UI)

## 🎯 사용법

1. 프론트엔드에서 YouTube URL 입력
2. AI가 자동으로 영상 분석 및 요약 생성
3. 내용에 맞는 시각화 자동 생성
4. 통합된 리포트 확인

## 🛠️ 기술 스택

### 백엔드
- **FastAPI**: 웹 프레임워크
- **LangGraph**: AI 워크플로우 관리
- **Claude AI (AWS Bedrock)**: 텍스트 분석 및 생성
- **VidCap API**: YouTube 자막 추출

### 프론트엔드
- **React**: UI 프레임워크
- **Chart.js**: 차트 시각화
- **Mermaid**: 다이어그램 생성

## 📊 시각화 타입

- **차트**: 막대, 선, 파이, 레이더, 산점도
- **다이어그램**: 플로우차트, 마인드맵, 관계도
- **테이블**: 데이터 비교 및 정리
- **고급 시각화**: D3.js 기반 커스텀 시각화

## 🔄 워크플로우

1. **자막 추출**: VidCap API로 YouTube 자막 획득
2. **포괄적 요약**: Claude AI가 상세한 요약 생성
3. **시각화 분석**: 내용을 분석하여 시각화 기회 탐지
4. **스마트 시각화**: 최적의 시각화 자동 생성
5. **리포트 통합**: 텍스트와 시각화를 통합한 최종 리포트

## 🚨 주의사항

- AWS Bedrock 사용 시 비용이 발생할 수 있습니다
- VidCap API 키가 필요합니다
- 영상에 자막이 없으면 분석이 제한됩니다

## 📝 라이선스

MIT License